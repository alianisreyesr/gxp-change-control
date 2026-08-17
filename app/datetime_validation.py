"""ISO 8601 date / date-time validation helpers (portfolio)."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

# Calendar date only: YYYY-MM-DD
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Common ISO-8601 datetime forms we accept (UTC preferred for audit-style stamps)
# Examples: 2026-08-17T04:20:00+00:00 | 2026-08-17T04:20:00Z | 2026-08-17T04:20:00.123456+00:00
DATETIME_HINT = (
    "Use ISO 8601: YYYY-MM-DD for dates, or YYYY-MM-DDThh:mm:ss[.fff]Z / ±hh:mm for date-times"
)


def parse_iso_date(value: str) -> date:
    if not isinstance(value, str) or not DATE_RE.match(value.strip()):
        raise ValueError(f"invalid date; expected YYYY-MM-DD. {DATETIME_HINT}")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid calendar date: {value}") from exp_or(exc)


def exp_or(exc: Exception) -> Exception:
    return exc


def parse_iso_datetime(value: str) -> datetime:
    """Parse ISO-8601 datetime; require timezone awareness (ALCOA contemporaneous theme)."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid date-time; empty. {DATETIME_HINT}")
    raw = value.strip()
    # Support trailing Z
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid date-time format. {DATETIME_HINT}") from exc
    if dt.tzinfo is None:
        raise ValueError(
            "date-time must include a timezone offset or Z (UTC); "
            "naive local timestamps are rejected for audit-style records"
        )
    return dt


def ensure_iso_datetime_str(value: str) -> str:
    """Validate and normalize to ISO string with offset."""
    dt = parse_iso_datetime(value)
    return dt.isoformat()


def ensure_iso_date_str(value: str) -> str:
    d = parse_iso_date(value)
    return d.isoformat()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_target_not_in_past(target: date, *, today: date | None = None) -> None:
    """Educational rule: planned implementation date should not be in the past."""
    ref = today or datetime.now(timezone.utc).date()
    if target < ref:
        raise ValueError(
            f"target_implementation_date {target.isoformat()} is in the past "
            f"(today UTC {ref.isoformat()}); use today or a future date"
        )
