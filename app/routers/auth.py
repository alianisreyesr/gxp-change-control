from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import (
    CurrentUser,
    LoginIn,
    Role,
    TokenOut,
    User,
    authenticate,
    create_access_token,
    require_roles,
)
from app.database import get_conn, log_security_event

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=TokenOut)
def login(body: LoginIn) -> TokenOut:
    user = authenticate(body.username, body.password)
    if user is None:
        log_security_event(body.username, "unauthenticated", "login_failed", "Invalid credentials")
        raise HTTPException(401, "Invalid username or password")
    return TokenOut(access_token=create_access_token(user), expires_in=3600, user=user)


@router.get("/me")
def me(user: CurrentUser):
    return user


AdminUser = Annotated[User, Depends(require_roles(Role.admin))]


@router.get("/security-events")
def security_events(_: AdminUser, limit: int = Query(default=50, ge=1, le=100)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"count": len(rows), "records": [dict(row) for row in rows]}
