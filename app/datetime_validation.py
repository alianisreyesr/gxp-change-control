"""ISO 8601 date / date-time / timezone validation (portfolio)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IANA_RE = re.compile(r"^[A-Za-z_]+(?:/[A-Za-z0-9_+\-]+)+$")

DATETIME_HINT = (
    "Use ISO 8601 date-time with timezone: "
    "YYYY-MM-DDThh:mm:ss[.fff]Z or YYYY-MM-DDThh:mm:ss±hh:mm. "
    "Naive (no zone) values are rejected."
)

MIN_OFFSET = timedelta(hours=-12)
MAX_OFFSET = timedelta(hours=14)

TIMEZONE_POLICY = (
    "timezone-aware-required; storage-normalized-to-UTC; "
    "local-wall-time-requires-fold-when-ambiguous"
)


class WallTimeKind(str, Enum):
    unique = "unique"
    ambiguous = "ambiguous"  # fall back — two UTC instants
    nonexistent = "nonexistent"  # spring forward — gap


@dataclass(frozen=True)
class FoldInstant:
    fold: Literal[0, 1]
    utc_iso: str
    utcoffset_seconds: int


@dataclass(frozen=True)
class WallTimeAnalysis:
    """Result of analyzing a naive local wall time in an IANA zone."""

    local_iso: str
    iana_zone: str
    kind: WallTimeKind
    message: str
    instants: tuple[FoldInstant, ...]  # 0, 1, or 2 depending on kind

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


def parse_iso_date(value: str) -> date:
    if not isinstance(value, str) or not DATE_RE.match(value.strip()):
        raise ValueError(f"invalid date; expected YYYY-MM-DD. {DATETIME_HINT}")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid calendar date: {value}") from exc


def _validate_offset_bounds(tzinfo: timezone | ZoneInfo, when: datetime) -> None:
    off = tzinfo.utcoffset(when)
    if off is None:
        raise ValueError("timezone produced no UTC offset")
    if off < MIN_OFFSET or off > MAX_OFFSET:
        raise ValueError(
            f"UTC offset {off} is outside the accepted civil range "
            f"[{MIN_OFFSET}, {MAX_OFFSET}]"
        )


def parse_iso_datetime(value: str) -> datetime:
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
    if dt.tzinfo is None:
        raise ValueError("cannot convert naive datetime to UTC")
    return dt.astimezone(timezone.utc)


def ensure_iso_datetime_str(value: str) -> str:
    dt = to_utc(parse_iso_datetime(value))
    return dt.isoformat()


def ensure_iso_date_str(value: str) -> str:
    return parse_iso_date(value).isoformat()


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


def _parse_naive_local(local_iso: str) -> datetime:
    if not isinstance(local_iso, str) or not local_iso.strip():
        raise ValueError("local_iso is required")
    raw = local_iso.strip()
    if raw.endswith("Z") or raw.endswith("z") or re.search(r"[+-]\d{2}:\d{2}$", raw):
        raise ValueError(
            "local_iso must be naive wall time (no Z/offset); "
            "use parse_iso_datetime for aware API stamps"
        )
    try:
        naive = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("invalid local ISO datetime") from exc
    if naive.tzinfo is not None:
        raise ValueError("local_iso must not already include a timezone offset")
    return naive


def _civil_tuple(dt: datetime) -> tuple[int, int, int, int, int, int, int]:
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)


def _fold_instant(naive: datetime, zi: ZoneInfo, fold: Literal[0, 1]) -> FoldInstant | None:
    """
    Attach fold and verify the wall time is a real civil time in this zone.

    Returns None if this fold does not correspond to a real local wall time
    (typical for the gap during spring-forward).
    """
    aware = naive.replace(tzinfo=zi, fold=fold)
    # A same-zone conversion is a no-op. Round-trip through UTC so ZoneInfo
    # normalizes gaps and overlaps before comparing the civil fields.
    back = aware.astimezone(timezone.utc).astimezone(zi)
    if _civil_tuple(back.replace(tzinfo=None)) != _civil_tuple(naive):
        return None
    # For ambiguous times both folds are real but offsets differ; for unique they match.
    off = aware.utcoffset()
    if off is None:
        return None
    utc = to_utc(aware)
    return FoldInstant(
        fold=fold,
        utc_iso=utc.isoformat(),
        utcoffset_seconds=int(off.total_seconds()),
    )


def analyze_wall_time(local_iso: str, iana_zone: str) -> WallTimeAnalysis:
    """
    Classify a naive local wall time in an IANA zone (PEP 495 fold).

    - **unique**: one UTC instant (fold 0 and 1 agree, or only one valid)
    - **ambiguous**: fall-back overlap — two UTC instants (fold=0 vs fold=1)
    - **nonexistent**: spring-forward gap — no valid fold
    """
    naive = _parse_naive_local(local_iso)
    zi = validate_iana_zone(iana_zone)
    local_norm = naive.isoformat(sep="T")

    f0 = _fold_instant(naive, zi, 0)
    f1 = _fold_instant(naive, zi, 1)

    if f0 is None and f1 is None:
        return WallTimeAnalysis(
            local_iso=local_norm,
            iana_zone=iana_zone,
            kind=WallTimeKind.nonexistent,
            message=(
                f"Local time {local_norm} does not exist in {iana_zone} "
                f"(DST spring-forward gap). Use a different local time or send UTC."
            ),
            instants=(),
        )

    # Both folds valid with different UTC → ambiguous
    if f0 is not None and f1 is not None and f0.utc_iso != f1.utc_iso:
        return WallTimeAnalysis(
            local_iso=local_norm,
            iana_zone=iana_zone,
            kind=WallTimeKind.ambiguous,
            message=(
                f"Local time {local_norm} is ambiguous in {iana_zone} "
                f"(DST fall-back). Specify fold=0 (first occurrence) or fold=1 "
                f"(second occurrence), or send an aware UTC timestamp."
            ),
            instants=(f0, f1),
        )

    chosen = f0 or f1
    if chosen is None:
        raise RuntimeError("wall-time analysis reached an invalid state")
    return WallTimeAnalysis(
        local_iso=local_norm,
        iana_zone=iana_zone,
        kind=WallTimeKind.unique,
        message=f"Local time {local_norm} maps to a single UTC instant in {iana_zone}.",
        instants=(chosen,),
    )


def convert_local_iso_to_utc(
    local_iso: str,
    iana_zone: str,
    *,
    fold: Optional[Literal[0, 1]] = None,
) -> str:
    """
    Convert naive local wall time + IANA zone → UTC ISO.

    - unique → converts without fold
    - nonexistent → ValueError
    - ambiguous → requires explicit fold=0 or fold=1
    """
    analysis = analyze_wall_time(local_iso, iana_zone)

    if analysis.kind is WallTimeKind.nonexistent:
        raise ValueError(analysis.message)

    if analysis.kind is WallTimeKind.ambiguous:
        if fold is None:
            raise ValueError(analysis.message)
        for inst in analysis.instants:
            if inst.fold == fold:
                return inst.utc_iso
        raise ValueError(f"fold must be 0 or 1; got {fold}")

    # unique — a fold value is meaningless here (only one instant exists), so any
    # caller-supplied fold is silently ignored rather than rejected.
    return analysis.instants[0].utc_iso


def timezone_policy_info() -> dict:
    return {
        "policy": TIMEZONE_POLICY,
        "accepted_on_api": ["ISO-8601 with Z", "ISO-8601 with numeric offset ±hh:mm"],
        "rejected": [
            "naive date-time on primary stamps",
            "US slash dates",
            "offsets outside UTC-12..UTC+14",
            "ambiguous local wall time without fold",
            "nonexistent local wall time (DST gap)",
        ],
        "storage": "UTC (normalized on write/validate)",
        "date_only": "YYYY-MM-DD (no timezone; calendar date)",
        "dst": {
            "fold": "PEP 495 — fold=0 first occurrence, fold=1 second during fall-back",
            "analyze": "GET/POST helpers under /meta/timezone/",
            "note": "America/Puerto_Rico has no DST; use America/New_York to demo gaps/ambiguity",
        },
        "examples": {
            "utc_z": "2026-08-17T12:00:00Z",
            "puerto_rico_ast": "2026-08-17T08:00:00-04:00",
            "nyc_ambiguous_local": "2025-11-02T01:30:00 + America/New_York",
            "nyc_gap_local": "2025-03-09T02:30:00 + America/New_York",
        },
    }
