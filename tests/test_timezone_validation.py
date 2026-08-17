"""Timezone validation policy tests."""

import pytest
from pydantic import ValidationError

from app.datetime_validation import (
    convert_local_iso_to_utc,
    ensure_iso_datetime_str,
    parse_iso_datetime,
    to_utc,
    validate_iana_zone,
)
from app.models import ChangeOut
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_zulu_normalizes_to_utc_offset():
    s = ensure_iso_datetime_str("2026-08-17T12:00:00Z")
    assert s.startswith("2026-08-17T12:00:00")
    assert "+00:00" in s or s.endswith("+00:00")


def test_offset_ast_converts_to_utc():
    # 08:00 AST (UTC-4) → 12:00 UTC
    s = ensure_iso_datetime_str("2026-08-17T08:00:00-04:00")
    assert "2026-08-17T12:00:00" in s


def test_naive_rejected():
    with pytest.raises(ValueError, match="timezone|naive"):
        parse_iso_datetime("2026-08-17T12:00:00")


def test_absurd_offset_rejected():
    with pytest.raises(ValueError, match="offset|range"):
        parse_iso_datetime("2026-08-17T12:00:00+23:00")


def test_iana_puerto_rico():
    zi = validate_iana_zone("America/Puerto_Rico")
    assert zi is not None


def test_iana_unknown():
    with pytest.raises(ValueError, match="unknown|invalid"):
        validate_iana_zone("Mars/Olympus")


def test_convert_local_pr_to_utc():
    utc = convert_local_iso_to_utc("2026-08-17T08:00:00", "America/Puerto_Rico")
    assert "2026-08-17T12:00:00" in utc


def test_convert_rejects_aware_local_iso():
    with pytest.raises(ValueError):
        convert_local_iso_to_utc("2026-08-17T08:00:00-04:00", "America/Puerto_Rico")


def test_change_out_normalizes_z():
    m = ChangeOut(
        id="CHG-ABCDEF",
        title="Title long enough",
        description="Description long enough for validation rules here.",
        system_name="Demo",
        change_type="code",
        priority="low",
        status="draft",
        requester="a.reyes",
        created_at="2026-08-17T12:00:00Z",
        updated_at="2026-08-17T12:00:00+00:00",
    )
    assert "+00:00" in m.created_at


def test_meta_timezone_policy_endpoint():
    r = client.get("/meta/timezone-policy")
    assert r.status_code == 200
    assert "UTC" in r.json()["storage"]


def test_meta_to_utc_endpoint():
    r = client.post(
        "/meta/timezone/to-utc",
        json={"local_iso": "2026-08-17T08:00:00", "iana_zone": "America/Puerto_Rico"},
    )
    assert r.status_code == 200
    assert "2026-08-17T12:00:00" in r.json()["utc_iso"]
