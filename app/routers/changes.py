from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, Role, User, require_roles
from app.database import get_conn, log_security_event
from app.datetime_validation import utc_now_iso
from app.deps import ActorParam, ChangeIdPath, StatusFilter
from app.models import (
    ActivityOut,
    ApprovalIn,
    ApprovalOut,
    ChangeCreate,
    ChangeOut,
    ImpactAssessmentIn,
    ImpactAssessmentOut,
)

router = APIRouter(prefix="/changes", tags=["changes"])
RequesterUser = Annotated[User, Depends(require_roles(Role.requester))]
AssessorUser = Annotated[User, Depends(require_roles(Role.assessor))]
ApproverUser = Annotated[User, Depends(require_roles(Role.quality_approver))]


def _deny(user: User, action: str, reason: str, change_id: str | None = None) -> None:
    log_security_event(user.username, user.role.value, action, reason, change_id)
    raise HTTPException(403, reason)


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
def create_change(body: ChangeCreate, user: RequesterUser):
    if user.role != Role.admin and body.requester != user.username:
        _deny(user, "create_change", "Requester must match the authenticated user")
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
        _log(conn, cid, user.username, "created", "Change request created")
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
def submit_change(change_id: ChangeIdPath, actor: ActorParam, user: RequesterUser):
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
    if not existing:
        raise HTTPException(404, "Change not found")
    if user.role != Role.admin and actor != user.username:
        _deny(user, "submit_change", "Actor must match the authenticated user", change_id)
    if user.role != Role.admin and existing["requester"] != user.username:
        _deny(user, "submit_change", "Only the requester may submit this change", change_id)
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
        _log(conn, change_id, user.username, "submitted", "Submitted for impact assessment")
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
    return _row_change(row)


@router.post("/{change_id}/impact", response_model=ImpactAssessmentOut)
def record_impact(change_id: ChangeIdPath, body: ImpactAssessmentIn, user: AssessorUser):
    if user.role != Role.admin and body.assessor != user.username:
        _deny(user, "record_impact", "Assessor must match the authenticated user", change_id)
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
                user.username,
                ts,
            ),
        )
        conn.execute(
            "UPDATE changes SET status = 'pending_approval', updated_at = ? WHERE id = ?",
            (ts, change_id),
        )
        _log(conn, change_id, user.username, "impact_complete", body.risk_summary[:200])
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
def approve_change(change_id: ChangeIdPath, body: ApprovalIn, user: ApproverUser):
    decision = body.decision  # PortfolioModel uses use_enum_values=True
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Change not found")
        if row["status"] != "pending_approval":
            raise HTTPException(400, f"Cannot decide from status={row['status']}")
        requester = row["requester"]
    if user.role != Role.admin and body.actor != user.username:
        _deny(user, "approve_change", "Actor must match the authenticated user", change_id)
    if user.role != Role.admin and body.role != "Quality":
        _deny(user, "approve_change", "Quality approvers must record the Quality approval role", change_id)
    if user.username == requester:
        _deny(user, "approve_change", "Segregation of duties: the requester cannot approve their own change", change_id)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        if not row or row["status"] != "pending_approval":
            raise HTTPException(409, "Change status changed during authorization; retry the decision")
        aid = f"APR-{uuid.uuid4().hex[:6].upper()}"
        ts = utc_now_iso()
        conn.execute(
            """
            INSERT INTO approvals (id, change_id, role, decision, comment, actor, decided_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (aid, change_id, body.role, decision, body.comment, user.username, ts),
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
        _log(conn, change_id, user.username, f"decision:{decision}", body.comment or "")
        apr = conn.execute("SELECT * FROM approvals WHERE id = ?", (aid,)).fetchone()
    return ApprovalOut(**dict(apr))


@router.post("/{change_id}/advance", response_model=ChangeOut)
def advance(change_id: ChangeIdPath, actor: ActorParam, user: CurrentUser):
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
        authorized_status = cur
    if user.role != Role.admin and actor != user.username:
        _deny(user, "advance_change", "Actor must match the authenticated user", change_id)
    required_role = {"approved": Role.implementer, "implementing": Role.verifier, "verification": Role.verifier}.get(cur)
    if required_role is not None and user.role not in (required_role, Role.admin):
        _deny(user, "advance_change", f"Role '{required_role.value}' is required from status={cur}", change_id)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
        cur = row["status"]
        if cur != authorized_status:
            raise HTTPException(409, "Change status changed during authorization; retry the transition")
        if cur not in transitions:
            raise HTTPException(400, f"No advance path from status={cur}")
        nxt = transitions[cur]
        conn.execute(
            "UPDATE changes SET status = ?, updated_at = ? WHERE id = ?",
            (nxt, utc_now_iso(), change_id),
        )
        _log(conn, change_id, user.username, "advanced", f"{cur} → {nxt}")
        row = conn.execute("SELECT * FROM changes WHERE id = ?", (change_id,)).fetchone()
    return _row_change(row)


@router.get("/{change_id}/activity", response_model=list[ActivityOut])
def activity(change_id: ChangeIdPath):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_log WHERE change_id = ? ORDER BY id DESC", (change_id,)
        ).fetchall()
    return [ActivityOut(**dict(r)) for r in rows]
