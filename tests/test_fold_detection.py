"""DST fold / gap detection tests (America/New_York transitions)."""

import pytest
from fastapi.testclient import TestClient

from app.datetime_validation import (
    WallTimeKind,
    analyze_wall_time,
    convert_local_iso_to_utc,
)
from app.main import app

client = TestClient(app)

NY = "America/New_York"
PR = "America/Puerto_Rico"

# US 2025 transitions (IANA):
# Spring forward: 2025-03-09 02:00 → 03:00 (02:30 nonexistent)
# Fall back:      2025-11-02 02:00 → 01:00 (01:30 ambiguous)


def test_unique_wall_time_pr():
    a = analyze_wall_time("2026-08-17T08:00:00", PR)
    assert a.kind is WallTimeKind.unique
    assert len(a.instants) == 1
    utc = convert_local_iso_to_utc("2026-08-17T08:00:00", PR)
    assert "2026-08-17T12:00:00" in utc


def test_nonexistent_spring_forward_nyc():
    a = analyze_wall_time("2025-03-09T02:30:00", NY)
    assert a.kind is WallTimeKind.nonexistent
    assert a.instants == ()
    with pytest.raises(ValueError, match="does not exist|gap|spring"):
        convert_local_iso_to_utc("2025-03-09T02:30:00", NY)


def test_ambiguous_fall_back_nyc():
    a = analyze_wall_time("2025-11-02T01:30:00", NY)
    assert a.kind is WallTimeKind.ambiguous
    assert len(a.instants) == 2
    assert a.instants[0].utc_iso != a.instants[1].utc_iso

    with pytest.raises(ValueError, match="ambiguous|fold"):
        convert_local_iso_to_utc("2025-11-02T01:30:00", NY)

    utc0 = convert_local_iso_to_utc("2025-11-02T01:30:00", NY, fold=0)
    utc1 = convert_local_iso_to_utc("2025-11-02T01:30:00", NY, fold=1)
    assert utc0 != utc1


def test_unique_ordinary_nyc():
    a = analyze_wall_time("2025-06-15T12:00:00", NY)
    assert a.kind is WallTimeKind.unique


def test_api_analyze_ambiguous():
    r = client.post(
        "/meta/timezone/analyze",
        json={"local_iso": "2025-11-02T01:30:00", "iana_zone": NY},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "ambiguous"
    assert len(body["instants"]) == 2


def test_api_to_utc_requires_fold_when_ambiguous():
    r = client.post(
        "/meta/timezone/to-utc",
        json={"local_iso": "2025-11-02T01:30:00", "iana_zone": NY},
    )
    assert r.status_code == 422

    r2 = client.post(
        "/meta/timezone/to-utc",
        json={"local_iso": "2025-11-02T01:30:00", "iana_zone": NY, "fold": 0},
    )
    assert r2.status_code == 200
    assert r2.json()["kind"] == "ambiguous"
    assert r2.json()["fold_used"] == 0


def test_api_gap_returns_422():
    r = client.post(
        "/meta/timezone/to-utc",
        json={"local_iso": "2025-03-09T02:30:00", "iana_zone": NY},
    )
    assert r.status_code == 422
