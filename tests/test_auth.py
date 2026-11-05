import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import database
from app.auth import Role, User, create_access_token
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "change_control.db")
    with TestClient(app) as test_client:
        yield test_client


def bearer(username: str, role: Role) -> dict[str, str]:
    token = create_access_token(User(username=username, role=role))
    return {"Authorization": f"Bearer {token}"}


def valid_change(requester: str = "requester.demo") -> dict:
    return {
        "title": "Protect workflow transitions with JWT",
        "description": "Require authenticated, role-bound identities for every mutating workflow action.",
        "system_name": "Demo QMS",
        "change_type": "code",
        "priority": "high",
        "requester": requester,
        "business_justification": "Remove spoofable actor identities from controlled workflow actions.",
    }


def test_login_returns_token_and_identity(client: TestClient):
    response = client.post("/auth/token", json={"username": "requester.demo", "password": "RequesterDemo!2026"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"] == {"username": "requester.demo", "role": "requester"}
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}).status_code == 200


def test_invalid_login_and_expired_token_are_rejected(client: TestClient):
    assert client.post("/auth/token", json={"username": "requester.demo", "password": "wrong-password"}).status_code == 401
    expired = create_access_token(User(username="requester.demo", role=Role.requester), expires_minutes=-1)
    response = client.post("/changes", json=valid_change(), headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_mutation_requires_authentication(client: TestClient):
    response = client.post("/changes", json=valid_change())
    assert response.status_code == 401


def test_requester_cannot_create_for_another_identity(client: TestClient):
    response = client.post(
        "/changes",
        json=valid_change("someone.else"),
        headers=bearer("requester.demo", Role.requester),
    )
    assert response.status_code == 403


def test_wrong_role_is_denied_and_security_event_is_recorded(client: TestClient):
    response = client.post(
        "/changes/CHG-1001/impact",
        json={
            "risk_summary": "A sufficiently detailed synthetic risk summary for authorization testing.",
            "residual_risk": "medium",
            "assessor": "requester.demo",
        },
        headers=bearer("requester.demo", Role.requester),
    )
    assert response.status_code == 403
    with sqlite3.connect(database.DB_PATH) as conn:
        event = conn.execute("SELECT actor, action FROM security_events ORDER BY id DESC LIMIT 1").fetchone()
    assert event == ("requester.demo", "authorization_denied")


def test_requester_can_create_own_change_and_cannot_spoof_actor(client: TestClient):
    headers = bearer("requester.demo", Role.requester)
    created = client.post("/changes", json=valid_change(), headers=headers)
    assert created.status_code == 201
    change_id = created.json()["id"]
    denied = client.post(f"/changes/{change_id}/submit?actor=someone.else", headers=headers)
    assert denied.status_code == 403


def test_transition_role_matrix_is_enforced(client: TestClient):
    with database.get_conn() as conn:
        conn.execute("UPDATE changes SET status = 'approved' WHERE id = 'CHG-1001'")
    denied = client.post(
        "/changes/CHG-1001/advance?actor=verifier.demo",
        headers=bearer("verifier.demo", Role.verifier),
    )
    assert denied.status_code == 403
    allowed = client.post(
        "/changes/CHG-1001/advance?actor=implementer.demo",
        headers=bearer("implementer.demo", Role.implementer),
    )
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "implementing"


def test_only_admin_can_read_security_events(client: TestClient):
    denied = client.get("/auth/security-events", headers=bearer("requester.demo", Role.requester))
    assert denied.status_code == 403
    allowed = client.get("/auth/security-events", headers=bearer("admin.demo", Role.admin))
    assert allowed.status_code == 200
    assert allowed.json()["count"] >= 1


def test_read_endpoints_require_authentication(client: TestClient):
    created = client.post(
        "/changes", json=valid_change(), headers=bearer("requester.demo", Role.requester)
    )
    assert created.status_code == 201
    change_id = created.json()["id"]
    paths = ["/changes", f"/changes/{change_id}", f"/changes/{change_id}/impact", f"/changes/{change_id}/activity"]
    for path in paths:
        assert client.get(path).status_code == 401, path
        assert client.get(path, headers=bearer("requester.demo", Role.requester)).status_code != 401, path


def _login(client: TestClient, password: str):
    return client.post("/auth/token", json={"username": "requester.demo", "password": password})


def test_login_expires_in_follows_configured_ttl(client: TestClient, monkeypatch):
    from app import auth

    assert _login(client, "RequesterDemo!2026").json()["expires_in"] == auth.ACCESS_TOKEN_TTL_SECONDS
    monkeypatch.setattr("app.routers.auth.ACCESS_TOKEN_TTL_SECONDS", 900)
    assert _login(client, "RequesterDemo!2026").json()["expires_in"] == 900


def test_login_is_throttled_after_repeated_failures(client: TestClient):
    from app.auth import login_throttle

    for _ in range(login_throttle.max_failures):
        assert _login(client, "wrong-password").status_code == 401
    blocked = _login(client, "RequesterDemo!2026")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    with sqlite3.connect(database.DB_PATH) as conn:
        action = conn.execute("SELECT action FROM security_events ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert action == "login_throttled"


def test_successful_login_resets_failure_counter(client: TestClient):
    from app.auth import login_throttle

    for _ in range(login_throttle.max_failures - 1):
        assert _login(client, "wrong-password").status_code == 401
    assert _login(client, "RequesterDemo!2026").status_code == 200
    assert _login(client, "wrong-password").status_code == 401  # counter restarted


def test_login_throttle_window_expires(monkeypatch):
    from app import auth

    throttle = auth.LoginThrottle(max_failures=2, window_seconds=10)
    clock = [1000.0]
    monkeypatch.setattr(auth.time, "monotonic", lambda: clock[0])
    throttle.record_failure("c", "u")
    throttle.record_failure("c", "U")
    assert throttle.retry_after("c", "u") > 0
    clock[0] += 11
    assert throttle.retry_after("c", "u") == 0


def test_jwt_secret_is_required_in_production(monkeypatch):
    from app import auth

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth._load_secret()
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth._load_secret()
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 40)
    assert auth._load_secret() == "x" * 40


def test_jwt_secret_in_development_uses_env_or_warns(monkeypatch):
    from app import auth

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", "dev-secret")
    assert auth._load_secret() == "dev-secret"
    monkeypatch.delenv("JWT_SECRET_KEY")
    with pytest.warns(UserWarning, match="ephemeral"):
        assert len(auth._load_secret()) >= 32
