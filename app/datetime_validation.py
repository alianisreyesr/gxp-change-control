"""ISO 8601 date / date-time / timezone validation (portfolio)."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Calendar date only: YYYY-MM-DD
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Numeric offset: +hh:mm, -hh:mm, +hhmm, -hhmm (after fromisoformat normalization we use ±hh:mm)
OFFSET_RE = re.compile(r"^([+-])(\d{2}):(\d{2})$")

# IANA name pattern (optional input style: append |America/Puerto_Rico — see parse docs)
IANA_RE = re.compile(r"^[A-Za-z_]+(?:/[A-Za-z0-9_+\-]+)+$")

DATETIME_HINT = (
    "Use ISO 8601 date-time with timezone: "
    "YYYY-MM-DDThh:mm:ss[.fff]Z or YYYY-MM-DDThh:mm:ss±hh:mm. "
    "Naive (no zone) values are rejected."
)

# Civil time offsets in use worldwide roughly span UTC−12 .. UTC+14
MIN_OFFSET = timedelta(hours=-12)
MAX_OFFSET = timedelta(hours=14)

# Policy name for logs / OpenAPI descriptions
TIMEZONE_POLICY = "timezone-aware-required; storage-normalized-to-UTC"


def parse_iso_date(value: str) -> date:
    if not isinstance(value, str) or not DATE_RE.match(value.strip()):
        raise ValueError(f"invalid date; expected YYYY-MM-DD. {DATETIME_HINT}")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid calendar date: {value}") from exc


def _validate_offset_bounds(tzinfo: timezone | ZoneInfo, when: datetime) -> None:
    """Reject absurd offsets outside the practical civil range."""
    # For fixed offsets, utcoffset is constant; for ZoneInfo it depends on `when`
    off = tzinfo.utcoffset(when)
    if off is None:
        raise ValueError("timezone produced no UTC offset")
    if off < MIN_OFFSET or off > MAX_OFFSET:
        raise ValueError(
            f"UTC offset {off} is outside the accepted civil range "
            f"[{MIN_OFFSET}, {MAX_OFFSET}]"
        )


def parse_iso_datetime(value: str) -> datetime:
    """
    Parse ISO-8601 datetime and **require** timezone awareness.

    Accepted:
      - ...Z (UTC)
      - ...+00:00 / ...-04:00 (numeric offsets)
      - Optional suffix ` IANA` is NOT part of pure ISO; use numeric/Z only for API bodies.

    Rejected:
      - Naive local timestamps (no offset / Z)
      - Offsets outside UTC−12 .. UTC+14
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid date-time; empty. {DATETIME_HINT}")
    raw = value.strip()

    if raw.endswith("Z") or raw.endswith("z"):
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

    _validate_offset_bounds(dt.tzinfo, dt)
    return dt


def to_utc(dt: datetime) -> datetime:
    """Normalize any aware datetime to UTC."""
    if dt.tzinfo is None:
        raise ValueError("cannot convert naive datetime to UTC")
    return dt.astimezone(timezone.utc)


def ensure_iso_datetime_str(value: str) -> str:
    """Validate, normalize to UTC, return ISO string with +00:00."""
    dt = to_utc(parse_iso_datetime(value))
    return dt.isoformat()


def ensure_iso_date_str(value: str) -> str:
    d = parse_iso_date(value)
    return d.isoformat()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_target_not_in_past(target: date, *, today: date | None = None) -> None:
    ref = today or datetime.now(timezone.utc).date()
    if target < ref:
        raise ValueError(
            f"target_implementation_date {target.isoformat()} is in the past "
            f"(today UTC {ref.isoformat()}); use today or a future date"
        )


def validate_iana_zone(name: str) -> ZoneInfo:
    """
    Validate an IANA time zone id (e.g. America/Puerto_Rico, UTC).

    Not used on primary API stamps (those use offsets/Z), but available for
    future UI localization and documentation of zone policy.
    """
    name = name.strip()
    if name.upper() in {"UTC", "GMT", "Z"}:
        return ZoneInfo("UTC")
    if not IANA_RE.match(name) and name != "UTC":
        raise ValueError(
            f"invalid IANA time zone id '{name}'; expected like America/Puerto_Rico or UTC"
        )
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown IANA time zone: {name}") from exc


def convert_local_iso_to_utc(local_iso: str, iana_zone: str) -> str:
    """
    Interpret a *naive* ISO local wall time in a named zone and return UTC ISO.

    Educational helper: demonstrates why the API rejects naive stamps without zone context.
    """
    if not isinstance(local_iso, str) or not local_iso.strip():
        raise ValueError("local_iso is required")
    raw = local_iso.strip()
    if raw.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", raw):
        raise ValueError("local_iso must be naive wall time; use parse_iso_datetime for aware values")
    try:
        naive = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("invalid local ISO datetime") from exc
    if naive.tzinfo is not None:
        raise ValueError("local_iso must not already include a timezone offset")
    zi = validate_iana_zone(iana_zone)
    aware = naive.replace(tzinfo=zi)
    _validate_offset_bounds(zi, aware)
    return to_utc(aware).isoformat()


def timezone_policy_info() -> dict:
    return {
        "policy": TIMEZONE_POLICY,
        "accepted_on_api": ["ISO-8601 with Z", "ISO-8601 with numeric offset ±hh:mm"],
        "rejected": ["naive date-time", "US slash dates", "offsets outside UTC-12..UTC+14"],
        "storage": "UTC (normalized on write/validate)",
        "date_only": "YYYY-MM-DD (no timezone; calendar date)",
        "iana_helper": "validate_iana_zone / convert_local_iso_to_utc for UI localization demos",
        "examples": {
            "utc_z": "2026-08-17T12:00:00Z",
            "utc_offset": "2026-08-17T12:00:00+00:00",
            "puerto_rico_ast": "2026-08-17T08:00:00-04:00",
        },
    }
