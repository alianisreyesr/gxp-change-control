"""FastAPI + Pydantic integration tests (422 contract)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["data_classification"] == "synthetic-portfolio-only"


def test_create_rejects_shared_actor_with_structured_422():
    r = client.post(
        "/changes",
        json={
            "title": "Update retention label copy",
            "description": "Change UI label only; no backend retention policy change.",
            "system_name": "Demo QMS",
            "change_type": "documentation",
            "priority": "medium",
            "requester": "admin",
        },
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "validation_error"
    assert isinstance(body["details"], list)
    assert any("actor" in d["msg"].lower() or "admin" in d["msg"].lower() for d in body["details"])


def test_create_rejects_extra_fields():
    r = client.post(
        "/changes",
        json={
            "title": "Meaningful title for change",
            "description": "Enough characters to pass the description minimum length.",
            "system_name": "Demo",
            "change_type": "code",
            "priority": "low",
            "requester": "a.reyes",
            "secret_field": "nope",
        },
    )
    assert r.status_code == 422


def test_create_accepts_valid_payload():
    r = client.post(
        "/changes",
        json={
            "title": "Meaningful title for change",
            "description": "Enough characters to pass the description minimum length.",
            "system_name": "Demo",
            "change_type": "code",
            "priority": "low",
            "requester": "a.reyes",
        },
    )
    assert r.status_code == 201
    assert r.json()["id"].startswith("CHG-")


def test_invalid_change_id_path_returns_422():
    r = client.get("/changes/not-a-valid-id")
    assert r.status_code == 422


def test_invalid_status_filter_returns_422():
    r = client.get("/changes?status=not_a_status")
    assert r.status_code == 422


def test_submit_rejects_forbidden_actor_query():
    # Use a known seed id that exists after init
    r = client.post("/changes/CHG-1001/submit?actor=admin")
    assert r.status_code == 422
