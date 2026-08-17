"""End-to-end API workflow tests for change control transitions."""

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Run workflow tests against an isolated SQLite database."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "change_control.db")
    with TestClient(app) as test_client:
        yield test_client


def create_change(client: TestClient) -> str:
    response = client.post(
        "/changes",
        json={
            "title": "Upgrade controlled reporting component",
            "description": (
                "Replace the synthetic reporting component while preserving the existing "
                "audit and authorization boundaries."
            ),
            "system_name": "Demo Quality Platform",
            "change_type": "code",
            "priority": "medium",
            "requester": "a.reyes",
            "business_justification": "Improve maintainability of the portfolio demonstration.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    return body["id"]


def submit_and_assess(client: TestClient, change_id: str) -> None:
    submitted = client.post(f"/changes/{change_id}/submit?actor=a.reyes")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "impact_assessment"

    assessment = client.post(
        f"/changes/{change_id}/impact",
        json={
            "affects_validated_state": True,
            "affects_part11_controls": False,
            "affects_data_integrity": True,
            "affects_training": False,
            "affects_sops": True,
            "risk_summary": (
                "The change touches the validated-state demonstration, data-integrity controls, "
                "and the supporting SOP narrative. Existing automated checks reduce residual risk."
            ),
            "residual_risk": "medium",
            "assessor": "q.analyst",
        },
    )
    assert assessment.status_code == 200
    assert assessment.json()["change_id"] == change_id

    current = client.get(f"/changes/{change_id}")
    assert current.status_code == 200
    assert current.json()["status"] == "pending_approval"


def test_complete_lifecycle_records_evidence_and_activity(client: TestClient):
    change_id = create_change(client)
    submit_and_assess(client, change_id)

    impact = client.get(f"/changes/{change_id}/impact")
    assert impact.status_code == 200
    assert impact.json()["residual_risk"] == "medium"
    assert impact.json()["affects_data_integrity"] is True

    approval = client.post(
        f"/changes/{change_id}/approve",
        json={
            "role": "Quality",
            "decision": "approve",
            "comment": "Approved after review of the synthetic impact evidence.",
            "actor": "q.approver",
        },
    )
    assert approval.status_code == 200
    assert approval.json()["decision"] == "approve"

    current = client.get(f"/changes/{change_id}")
    assert current.json()["status"] == "approved"

    for expected_status in ("implementing", "verification", "closed"):
        advanced = client.post(f"/changes/{change_id}/advance?actor=i.owner")
        assert advanced.status_code == 200
        assert advanced.json()["status"] == expected_status

    activity = client.get(f"/changes/{change_id}/activity")
    assert activity.status_code == 200
    actions = [entry["action"] for entry in activity.json()]
    assert "created" in actions
    assert "submitted" in actions
    assert "impact_complete" in actions
    assert "decision:approve" in actions
    assert actions.count("advanced") == 3


def test_reject_and_request_info_return_change_for_rework(client: TestClient):
    change_id = create_change(client)
    submit_and_assess(client, change_id)

    rejected = client.post(
        f"/changes/{change_id}/approve",
        json={
            "role": "Quality",
            "decision": "reject",
            "comment": "The risk rationale needs a clearer mitigation plan.",
            "actor": "q.approver",
        },
    )
    assert rejected.status_code == 200
    assert client.get(f"/changes/{change_id}").json()["status"] == "rejected"

    resubmitted = client.post(f"/changes/{change_id}/submit?actor=a.reyes")
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "impact_assessment"

    revised = client.post(
        f"/changes/{change_id}/impact",
        json={
            "affects_validated_state": True,
            "affects_part11_controls": False,
            "affects_data_integrity": True,
            "affects_training": False,
            "affects_sops": False,
            "risk_summary": (
                "The revised assessment adds automated regression checks and an explicit rollback "
                "step, reducing the remaining demonstration risk to medium."
            ),
            "residual_risk": "medium",
            "assessor": "q.analyst",
        },
    )
    assert revised.status_code == 200

    more_info = client.post(
        f"/changes/{change_id}/approve",
        json={
            "role": "Quality",
            "decision": "request_info",
            "comment": "Attach the synthetic rollback evidence before approval.",
            "actor": "q.approver",
        },
    )
    assert more_info.status_code == 200
    assert client.get(f"/changes/{change_id}").json()["status"] == "impact_assessment"

    actions = [
        entry["action"] for entry in client.get(f"/changes/{change_id}/activity").json()
    ]
    assert "decision:reject" in actions
    assert "decision:request_info" in actions


def test_invalid_advance_does_not_add_activity(client: TestClient):
    change_id = create_change(client)
    before = client.get(f"/changes/{change_id}/activity").json()

    response = client.post(f"/changes/{change_id}/advance?actor=a.reyes")
    assert response.status_code == 400
    assert response.json()["detail"] == "No advance path from status=draft"

    after = client.get(f"/changes/{change_id}/activity").json()
    assert after == before
