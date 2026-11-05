from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    CurrentUser,
    LoginIn,
    Role,
    TokenOut,
    User,
    authenticate,
    create_access_token,
    login_throttle,
    require_roles,
)
from app.database import get_conn, log_security_event

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=TokenOut)
def login(body: LoginIn, request: Request) -> TokenOut:
    client = request.client.host if request.client else "unknown"
    # Control characters are stripped so attacker-supplied names cannot forge log lines.
    safe_username = "".join(ch for ch in body.username if ch.isprintable())[:80]
    retry_after = login_throttle.retry_after(client, body.username)
    if retry_after:
        log_security_event(safe_username, "unauthenticated", "login_throttled", "Too many failed attempts")
        raise HTTPException(
            429,
            "Too many failed login attempts; try again later",
            headers={"Retry-After": str(retry_after)},
        )
    user = authenticate(body.username, body.password)
    if user is None:
        login_throttle.record_failure(client, body.username)
        log_security_event(safe_username, "unauthenticated", "login_failed", "Invalid credentials")
        raise HTTPException(401, "Invalid username or password")
    login_throttle.reset(client, body.username)
    return TokenOut(access_token=create_access_token(user), expires_in=ACCESS_TOKEN_TTL_SECONDS, user=user)


@router.get("/me")
def me(user: CurrentUser):
    return user


AdminUser = Annotated[User, Depends(require_roles(Role.admin))]


@router.get("/security-events")
def security_events(_: AdminUser, limit: int = Query(default=50, ge=1, le=100)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"count": len(rows), "records": [dict(row) for row in rows]}
