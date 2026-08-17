"""FastAPI + Pydantic integration tests (422 contract)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import APP_VERSION, app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Run each API test against an isolated database with app lifespan enabled."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "change_control.db")
    with TestClient(app) as test_client:
        yield test_client


def test_health_ok(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["data_classification"] == "synthetic-portfolio-only"
    assert body["version"] == APP_VERSION
    assert app.version == APP_VERSION

    root = Path(__file__).resolve().parents[1]
    package = json.loads((root / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert package["version"] == APP_VERSION

    sonar = (root / "sonar-project.properties").read_text(encoding="utf-8")
    assert f"sonar.projectVersion={APP_VERSION}" in sonar

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{APP_VERSION}]" in changelog

    release_notes = root / "docs" / "releases" / f"v{APP_VERSION}.md"
    assert release_notes.is_file()

    release_workflow = root / ".github" / "workflows" / "release.yml"
    assert release_workflow.is_file()


def test_create_rejects_shared_actor_with_structured_422(client: TestClient):
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


def test_create_rejects_extra_fields(client: TestClient):
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


def test_create_accepts_valid_payload(client: TestClient):
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


def test_invalid_change_id_path_returns_422(client: TestClient):
    r = client.get("/changes/not-a-valid-id")
    assert r.status_code == 422


def test_invalid_status_filter_returns_422(client: TestClient):
    r = client.get("/changes?status=not_a_status")
    assert r.status_code == 422


def test_submit_rejects_forbidden_actor_query(client: TestClient):
    # Use a known seed id that exists after init
    r = client.post("/changes/CHG-1001/submit?actor=admin")
    assert r.status_code == 422
