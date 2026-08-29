from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.database import get_conn
from app.datetime_validation import utc_now_iso
from app.deps import ActorParam, ChangeIdPath, StatusFilter
from app.models import (
    ApprovalIn,
    ApprovalOut,
    ActivityOut,
    ChangeCreate,
    ChangeOut,
    ImpactAssessmentIn,
    ImpactAssessmentOut,
)

router = APIRouter(prefix="/changes", tags=["changes"])


def _row_change(row) -> ChangeOut:
    data = dict(row)
    if "target_implementation_date" not in data:
        data["target_implementation_date"] = None
    return ChangeOut(**data)


def _log(conn, change_id: str, actor: str, action: str, detail: str = "") -> None:
    conn.execute(
        "INSERT INTO activity_log (change_id, actor, action, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (change_id, actor, action, detail, utc_now_iso()),
    )


@router.get("", response_model=list[ChangeOut])
def list_changes(status: StatusFilter = None):
    with get_conn() as conn:
        if status is not None:
            rows = conn.execute(
                "SELECT * FROM changes WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM changes ORDER BY updated_at DESC").fetchall()
    return [_row_change(r) for r in rows]


@router.post("", response_model=ChangeOut, status_code=201)
def create_change(body: ChangeCreate):
    cid = f"CHG-{uuid.uuid4().hex[:6].upper()}"
    ts = utc_now_iso()
    # PortfolioModel uses use_enum_values=True, so these are already plain strings.
    change_type = body.change_type
    priority = body.priority
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO changes (
              id, title, description, system_name, change_type, priority, status,
              requester, business_justification, target_implementation_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?)
            """,
            (
                cid,
                body.title,
                body.description,
                body.system_name,
                change_type,
                priority,
                body.requester,
                body.business_justification,
                body.target_implementation_date,
                ts,
                ts,
            ),
        )
        _log(conn, cid, body.requester, "created", "Change request created")
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (cid,)).fetchone()
    return _row_change(row)


@router.get("/{change_id}", response_model=ChangeOut)
def get_change(change_id: ChangeIdPath):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Change not found")
    return _row_change(row)


@router.post("/{change_id}/submit", response_model=ChangeOut)
def submit_change(change_id: ChangeIdPath, actor: ActorParam):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Change not found")
        if row["status"] not in ("draft", "rejected"):
            raise HTTPException(400, f"Cannot submit from status={row['status']}")
        conn.execute(
            "UPDATE changes SET status = 'impact_assessment', updated_at = ? WHERE id = ?",
            (utc_now_iso(), change_id),
        )
        _log(conn, change_id, actor, "submitted", "Submitted for impact assessment")
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
    return _row_change(row)


@router.post("/{change_id}/impact", response_model=ImpactAssessmentOut)
def record_impact(change_id: ChangeIdPath, body: ImpactAssessmentIn):
    residual = body.residual_risk  # PortfolioModel uses use_enum_values=True
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Change not found")
        if row["status"] != "impact_assessment":
            raise HTTPException(400, f"Cannot assess impact from status={row['status']}")
        ia_id = f"IA-{uuid.uuid4().hex[:6].upper()}"
        ts = utc_now_iso()
        conn.execute("DELETE FROM impact_assessments WHERE change_id = ?", (change_id,))
        conn.execute(
            """
            INSERT INTO impact_assessments (
              id, change_id, affects_validated_state, affects_part11_controls,
              affects_data_integrity, affects_training, affects_sops,
              risk_summary, residual_risk, assessor, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ia_id,
                change_id,
                int(body.affects_validated_state),
                int(body.affects_part11_controls),
                int(body.affects_data_integrity),
                int(body.affects_training),
                int(body.affects_sops),
                body.risk_summary,
                residual,
                body.assessor,
                ts,
            ),
        )
        conn.execute(
            "UPDATE changes SET status = 'pending_approval', updated_at = ? WHERE id = ?",
            (ts, change_id),
        )
        _log(conn, change_id, body.assessor, "impact_complete", body.risk_summary[:200])
        ia = conn.execute("SELECT * FROM impact_assessments WHERE id = ?", (ia_id,)).fetchone()
    data = dict(ia)
    for k in (
        "affects_validated_state",
        "affects_part11_controls",
        "affects_data_integrity",
        "affects_training",
        "affects_sops",
    ):
        data[k] = bool(data[k])
    return ImpactAssessmentOut(**data)


@router.get("/{change_id}/impact", response_model=ImpactAssessmentOut)
def get_impact(change_id: ChangeIdPath):
    with get_conn() as conn:
        ia = conn.execute(
            "SELECT * FROM impact_assessments WHERE change_id = ?", (change_id,)
        ).fetchone()
    if not ia:
        raise HTTPException(404, "Impact assessment not found")
    data = dict(ia)
    for k in (
        "affects_validated_state",
        "affects_part11_controls",
        "affects_data_integrity",
        "affects_training",
        "affects_sops",
    ):
        data[k] = bool(data[k])
    return ImpactAssessmentOut(**data)


@router.post("/{change_id}/approve", response_model=ApprovalOut)
def approve_change(change_id: ChangeIdPath, body: ApprovalIn):
    decision = body.decision  # PortfolioModel uses use_enum_values=True
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Change not found")
        if row["status"] != "pending_approval":
            raise HTTPException(400, f"Cannot decide from status={row['status']}")
        aid = f"APR-{uuid.uuid4().hex[:6].upper()}"
        ts = utc_now_iso()
        conn.execute(
            """
            INSERT INTO approvals (id, change_id, role, decision, comment, actor, decided_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (aid, change_id, body.role, decision, body.comment, body.actor, ts),
        )
        if decision == "approve":
            new_status = "approved"
        elif decision == "reject":
            new_status = "rejected"
        else:
            new_status = "impact_assessment"
        conn.execute(
            "UPDATE changes SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, ts, change_id),
        )
        _log(conn, change_id, body.actor, f"decision:{decision}", body.comment or "")
        apr = conn.execute("SELECT * FROM approvals WHERE id = ?", (aid,)).fetchone()
    return ApprovalOut(**dict(apr))


@router.post("/{change_id}/advance", response_model=ChangeOut)
def advance(change_id: ChangeIdPath, actor: ActorParam):
    transitions = {
        "approved": "implementing",
        "implementing": "verification",
        "verification": "closed",
    }
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Change not found")
        cur = row["status"]
        if cur not in transitions:
            raise HTTPException(400, f"No advance path from status={cur}")
        nxt = transitions[cur]
        conn.execute(
            "UPDATE changes SET status = ?, updated_at = ? WHERE id = ?",
            (nxt, utc_now_iso(), change_id),
        )
        _log(conn, change_id, actor, "advanced", f"{cur} → {nxt}")
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
    return _row_change(row)


@router.get("/{change_id}/activity", response_model=list[ActivityOut])
def activity(change_id: ChangeIdPath):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_log WHERE change_id = ? ORDER BY id DESC", (change_id,)
        ).fetchall()
    return [ActivityOut(**dict(r)) for r in rows]
