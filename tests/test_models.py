"""Pydantic validation unit tests — portfolio prototype."""

import pytest
from pydantic import ValidationError

from app.models import ApprovalIn, ChangeCreate, ImpactAssessmentIn


def test_change_create_strips_and_accepts_valid():
    m = ChangeCreate(
        title="  Align severity labels with SOP  ",
        description="Update dropdown labels only; no scoring logic changes in this request.",
        system_name="Deviation Monitor",
        change_type="configuration",
        priority="medium",
        requester="a.reyes",
    )
    assert m.title == "Align severity labels with SOP"
    assert m.requester == "a.reyes"


def test_forbidden_shared_actor():
    with pytest.raises(ValidationError) as exc:
        ChangeCreate(
            title="Meaningful change title here",
            description="Enough detail about what will change in the controlled system.",
            system_name="LIMS demo",
            change_type="code",
            requester="admin",
        )
    assert "not allowed" in str(exc.value).lower() or "attributable" in str(exc.value).lower()


def test_high_priority_requires_justification():
    with pytest.raises(ValidationError):
        ChangeCreate(
            title="Emergency patch for label printer queue",
            description="Apply hotfix to queue worker for stuck jobs in demo environment only.",
            system_name="Print queue",
            change_type="code",
            priority="critical",
            requester="j.martinez",
            business_justification="too short",
        )


def test_reject_requires_comment():
    with pytest.raises(ValidationError):
        ApprovalIn(role="Quality", decision="reject", actor="q.lead", comment=None)


def test_approve_without_comment_ok():
    m = ApprovalIn(role="Quality", decision="approve", actor="q.lead")
    assert m.decision in ("approve",)


def test_impact_high_residual_needs_long_summary():
    with pytest.raises(ValidationError):
        ImpactAssessmentIn(
            risk_summary="Too short for high residual risk.",
            residual_risk="high",
            assessor="q.analyst",
            affects_validated_state=True,
        )


def test_impact_valid():
    m = ImpactAssessmentIn(
        risk_summary=(
            "Documentation-only impact; validated functional behavior unchanged. "
            "SOP cross-reference update planned."
        ),
        residual_risk="low",
        assessor="q.analyst",
        affects_sops=True,
    )
    assert m.affects_sops is True
