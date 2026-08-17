from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "change_control.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(schema)
        count = conn.execute("SELECT COUNT(*) AS c FROM changes").fetchone()["c"]
        if count == 0:
            _seed(conn)


def _seed(conn: sqlite3.Connection) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    samples = [
        (
            "CHG-1001",
            "Update deviation severity dropdown labels",
            "Align UI labels with SOP-QA-014 terminology. No business rule changes.",
            "Quality Deviation Risk Monitor (demo)",
            "configuration",
            "medium",
            "impact_assessment",
            "a.reyes",
            "Inspector-facing terminology consistency.",
            now,
            now,
        ),
        (
            "CHG-1002",
            "Add rate-limit headers to public API responses",
            "Expose standard rate-limit response headers for client observability.",
            "Portfolio API gateway (demo)",
            "code",
            "low",
            "pending_approval",
            "j.martinez",
            "Improve client diagnostics without changing authorization model.",
            now,
            now,
        ),
        (
            "CHG-1003",
            "Rotate synthetic seed data generator seed",
            "Refresh demo dataset for portfolio screenshots; no production systems.",
            "CSV Evidence Tracker (demo)",
            "documentation",
            "low",
            "closed",
            "a.reyes",
            "Keep demo data clearly fictional and current.",
            now,
            now,
        ),
    ]
    conn.executemany(
        """
        INSERT INTO changes (
          id, title, description, system_name, change_type, priority, status,
          requester, business_justification, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        samples,
    )
    conn.execute(
        """
        INSERT INTO impact_assessments (
          id, change_id, affects_validated_state, affects_part11_controls,
          affects_data_integrity, affects_training, affects_sops,
          risk_summary, residual_risk, assessor, assessed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "IA-1002",
            "CHG-1002",
            0,
            0,
            0,
            0,
            1,
            "Documentation of API behavior only; no change to audit trail or auth.",
            "low",
            "q.analyst",
            now,
        ),
    )
    for cid, action, detail in [
        ("CHG-1001", "created", "Change draft created"),
        ("CHG-1001", "submitted", "Submitted for impact assessment"),
        ("CHG-1002", "created", "Change draft created"),
        ("CHG-1002", "impact_complete", "Impact assessment recorded"),
        ("CHG-1003", "closed", "Demo data refresh completed and closed"),
    ]:
        conn.execute(
            "INSERT INTO activity_log (change_id, actor, action, detail, created_at) VALUES (?, ?, ?, ?, ?)",
            (cid, "system", action, detail, now),
        )
