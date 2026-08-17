"""ISO date / date-time validation tests."""

import pytest
from pydantic import ValidationError

from app.datetime_validation import parse_iso_date, parse_iso_datetime
from app.models import ChangeCreate, ChangeOut


def test_parse_date_ok():
    assert parse_iso_date("2026-09-01").isoformat() == "2026-09-01"


def test_parse_date_rejects_us_format():
    with pytest.raises(ValueError):
        parse_iso_date("09/01/2026")


def test_parse_datetime_requires_tz():
    with pytest.raises(ValueError, match="timezone"):
        parse_iso_datetime("2026-08-17T12:00:00")


def test_parse_datetime_zulu():
    dt = parse_iso_datetime("2026-08-17T12:00:00Z")
    assert dt.tzinfo is not None


def test_change_create_rejects_past_target_date():
    with pytest.raises(ValidationError):
        ChangeCreate(
            title="Meaningful change title x",
            description="Enough characters for the description minimum length here.",
            system_name="Demo",
            change_type="code",
            priority="low",
            requester="a.reyes",
            target_implementation_date="2020-01-01",
        )


def test_change_create_accepts_future_date():
    m = ChangeCreate(
        title="Meaningful change title x",
        description="Enough characters for the description minimum length here.",
        system_name="Demo",
        change_type="code",
        priority="low",
        requester="a.reyes",
        target_implementation_date="2099-12-31",
    )
    assert m.target_implementation_date == "2099-12-31"


def test_change_out_validates_created_at():
    with pytest.raises(ValidationError):
        ChangeOut(
            id="CHG-ABCDEF",
            title="t",
            description="d" * 20,
            system_name="s",
            change_type="code",
            priority="low",
            status="draft",
            requester="a.reyes",
            created_at="not-a-date",
            updated_at="2026-08-17T12:00:00Z",
        )
