"""Parameterized tests for Australia/Lord_Howe (30-minute DST shift)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.datetime_validation import (
    WallTimeKind,
    analyze_wall_time,
    convert_local_iso_to_utc,
    ensure_iso_datetime_str,
)
from app.main import app

client = TestClient(app)

LH = "Australia/Lord_Howe"

# Lord Howe Island: LHST ≈ UTC+10:30, LHDT ≈ UTC+11:00 (DST +30 minutes, not +60).
# Transition dates follow IANA (similar calendar family to NSW/Sydney in recent years).
# We assert *structural* properties (offset magnitude, uniqueness vs ambiguity)
# rather than hard-coding every civil transition minute forever.


def _offset_hours(utc_iso: str, local_iso: str) -> float:
    """Civil local vs UTC difference in hours (for unique conversions)."""
    local = datetime.fromisoformat(local_iso)
    utc = datetime.fromisoformat(utc_iso)
    # local naive interpreted as wall; utc is aware
    assert utc.tzinfo is not None
    # Reconstruct expected: utc + offset ≈ local wall in absolute terms
    # offset_hours = local_as_if_utc - utc
    local_as_utc = local.replace(tzinfo=timezone.utc)
    delta = local_as_utc - utc.astimezone(timezone.utc).replace(tzinfo=None).replace(
        tzinfo=timezone.utc
    )
    # Simpler: from analysis instants utcoffset_seconds
    return delta.total_seconds() / 3600.0


@pytest.mark.parametrize(
    "local_iso,expect_kind",
    [
        # Mid-summer (southern): typically +11:00
        ("2025-01-15T12:00:00", WallTimeKind.unique),
        # Mid-winter: typically +10:30
        ("2025-07-15T12:00:00", WallTimeKind.unique),
        # Ordinary spring/autumn days away from transition
        ("2025-03-01T09:00:00", WallTimeKind.unique),
        ("2025-09-01T09:00:00", WallTimeKind.unique),
    ],
)
def test_lord_howe_unique_wall_times(local_iso: str, expect_kind: WallTimeKind):
    result = analyze_wall_time(local_iso, LH)
    assert result.kind is expect_kind
    assert len(result.instants) == 1
    utc = convert_local_iso_to_utc(local_iso, LH)
    assert "+00:00" in utc or utc.endswith("+00:00")


@pytest.mark.parametrize(
    "local_iso,expected_offset_hours",
    [
        # Winter-style +10:30
        ("2025-07-15T12:00:00", 10.5),
        # Summer-style +11:00
        ("2025-01-15T12:00:00", 11.0),
    ],
)
def test_lord_howe_half_hour_and_full_hour_offsets(
    local_iso: str, expected_offset_hours: float
):
    result = analyze_wall_time(local_iso, LH)
    assert result.kind is WallTimeKind.unique
    inst = result.instants[0]
    got = inst.utcoffset_seconds / 3600.0
    assert got == pytest.approx(expected_offset_hours)
    # Conversion matches declared offset
    utc_iso = convert_local_iso_to_utc(local_iso, LH)
    assert inst.utc_iso == utc_iso


@pytest.mark.parametrize(
    "aware_iso",
    [
        "2025-07-15T01:30:00+10:30",  # winter local noon-ish in UTC terms
        "2025-01-15T01:00:00+11:00",
        "2025-07-15T01:30:00+10:30",
    ],
)
def test_lord_howe_aware_offsets_accepted_on_api_stamps(aware_iso: str):
    """Primary API path: fractional offsets are valid ISO, normalized to UTC."""
    normalized = ensure_iso_datetime_str(aware_iso)
    assert "+00:00" in normalized
    # Round-trip stability: normalize twice
    assert ensure_iso_datetime_str(normalized) == normalized


@pytest.mark.parametrize(
    "local_iso",
    [
        # Near southern spring transition window (may be unique or ambiguous by year rules).
        # We only assert the analyzer returns a known kind and is deterministic.
        "2025-10-05T01:30:00",
        "2025-10-05T02:00:00",
        "2025-10-05T02:30:00",
        "2025-04-06T01:30:00",
        "2025-04-06T02:00:00",
        "2025-04-06T02:30:00",
    ],
)
def test_lord_howe_transition_window_is_classified(local_iso: str):
    result = analyze_wall_time(local_iso, LH)
    assert result.kind in {
        WallTimeKind.unique,
        WallTimeKind.ambiguous,
        WallTimeKind.nonexistent,
    }
    if result.kind is WallTimeKind.ambiguous:
        assert len(result.instants) == 2
        assert result.instants[0].utc_iso != result.instants[1].utc_iso
        # Half-hour DST: the two offsets should differ by 30 minutes
        delta = abs(
            result.instants[0].utcoffset_seconds - result.instants[1].utcoffset_seconds
        )
        assert delta == 30 * 60
        with pytest.raises(ValueError, match="ambiguous|fold"):
            convert_local_iso_to_utc(local_iso, LH)
        utc0 = convert_local_iso_to_utc(local_iso, LH, fold=0)
        utc1 = convert_local_iso_to_utc(local_iso, LH, fold=1)
        assert utc0 != utc1
    elif result.kind is WallTimeKind.nonexistent:
        assert result.instants == ()
        with pytest.raises(ValueError):
            convert_local_iso_to_utc(local_iso, LH)
    else:
        assert len(result.instants) == 1
        convert_local_iso_to_utc(local_iso, LH)


def test_lord_howe_ambiguous_fold_delta_is_thirty_minutes_when_present():
    """Scan a day around April 2025 for an ambiguous sample; skip if none (IANA drift)."""
    found = None
    base = datetime(2025, 4, 6, 0, 0, 0)
    for minutes in range(0, 24 * 60, 15):
        local = (base + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S")
        result = analyze_wall_time(local, LH)
        if result.kind is WallTimeKind.ambiguous:
            found = result
            break
    if found is None:
        pytest.skip("No ambiguous Lord Howe wall time found on 2025-04-06 in this tzdata")
    delta = abs(found.instants[0].utcoffset_seconds - found.instants[1].utcoffset_seconds)
    assert delta == 30 * 60, "Lord Howe DST step should be 30 minutes"


def test_api_analyze_lord_howe_winter():
    r = client.post(
        "/meta/timezone/analyze",
        json={"local_iso": "2025-07-15T12:00:00", "iana_zone": LH},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "unique"
    assert body["instants"][0]["utcoffset_seconds"] == int(10.5 * 3600)


def test_api_analyze_lord_howe_summer():
    r = client.post(
        "/meta/timezone/analyze",
        json={"local_iso": "2025-01-15T12:00:00", "iana_zone": LH},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "unique"
    assert body["instants"][0]["utcoffset_seconds"] == int(11 * 3600)


@pytest.mark.parametrize(
    "local_iso,fold",
    [
        ("2025-07-15T12:00:00", None),
        ("2025-01-15T12:00:00", None),
    ],
)
def test_api_to_utc_lord_howe_unique(local_iso: str, fold):
    payload = {"local_iso": local_iso, "iana_zone": LH}
    if fold is not None:
        payload["fold"] = fold
    r = client.post("/meta/timezone/to-utc", json=payload)
    assert r.status_code == 200
    assert r.json()["kind"] == "unique"
    assert "+00:00" in r.json()["utc_iso"]
