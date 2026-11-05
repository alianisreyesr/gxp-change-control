"""JWT authentication and role authorization for the portfolio demo."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import threading
import time
import warnings
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


class Role(str, Enum):
    requester = "requester"
    assessor = "assessor"
    quality_approver = "quality_approver"
    implementer = "implementer"
    verifier = "verifier"
    admin = "admin"


class User(BaseModel):
    username: str
    role: Role


class LoginIn(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


# PBKDF2 hashes for documented, synthetic demo accounts only. No plaintext
# credentials or production identities are stored in the application.
_USERS = {
    "requester.demo": (Role.requester, "6778702d7265717565737465722e64656d6f", "34de7a35b43531735012f158fb84aadb7757b3f4eea5ac28da43d4839c33c83f"),
    "assessor.demo": (Role.assessor, "6778702d6173736573736f722e64656d6f", "f850bc38d437d152a8dc10032db8cb1636807c54ece944e2502f78fe02305552"),
    "quality.demo": (Role.quality_approver, "6778702d7175616c6974792e64656d6f", "9ba1eca459a04ddd17467a83b284aaec47c1768c54a995752151213b734c9527"),
    "implementer.demo": (Role.implementer, "6778702d696d706c656d656e7465722e64656d6f", "5bf31a73bb33622a0f273c87a59a6f1ef2c05f9f27df568f6e92e3f11a3386bf"),
    "verifier.demo": (Role.verifier, "6778702d76657269666965722e64656d6f", "e03a46d1e0f13ee433100231481f2a9d878d63970badcc05a5d266213a5064e9"),
    "admin.demo": (Role.admin, "6778702d61646d696e2e64656d6f", "2ae159df8e7108f3f1ed00fb7f3636e46fb2a04b561680a8fe821094d8c8d134"),
}
_ALGORITHM = "HS256"
_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
_PRODUCTION_ENVIRONMENTS = {"production", "prod", "staging"}
_MIN_SECRET_LENGTH = 32


def _load_secret() -> str:
    """Return the JWT signing key from JWT_SECRET_KEY.

    Production-like environments (ENVIRONMENT=production|prod|staging) must provide a
    strong, stable secret; startup fails otherwise. In development an ephemeral random
    secret is generated, so tokens are invalidated on every restart and do not work
    across multiple workers.
    """
    configured = os.getenv("JWT_SECRET_KEY")
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    if environment in _PRODUCTION_ENVIRONMENTS:
        if not configured or len(configured) < _MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"JWT_SECRET_KEY must be set to at least {_MIN_SECRET_LENGTH} characters "
                f"when ENVIRONMENT={environment}"
            )
        return configured
    if configured:
        return configured
    warnings.warn(
        "JWT_SECRET_KEY is not set; using an ephemeral secret (tokens reset on restart). "
        "Set JWT_SECRET_KEY for any shared or production deployment.",
        stacklevel=2,
    )
    return secrets.token_urlsafe(48)


_SECRET = _load_secret()
ACCESS_TOKEN_TTL_SECONDS = _EXPIRES_MINUTES * 60
_bearer = HTTPBearer(auto_error=False)


class LoginThrottle:
    """In-memory sliding-window limiter for failed logins (per client + username).

    Process-local by design for this demo; a multi-worker deployment needs a shared
    store (e.g. Redis) or a rate-limiting reverse proxy in front of the API.
    """

    def __init__(self, max_failures: int, window_seconds: int) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[tuple[str, str], list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: tuple[str, str], now: float) -> list[float]:
        cutoff = now - self.window_seconds
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def retry_after(self, client: str, username: str) -> int:
        """Seconds until another attempt is allowed (0 when not throttled)."""
        key = (client, username.lower())
        with self._lock:
            now = time.monotonic()
            recent = self._recent(key, now)
            if len(recent) < self.max_failures:
                return 0
            return max(1, int(recent[0] + self.window_seconds - now) + 1)

    def record_failure(self, client: str, username: str) -> None:
        key = (client, username.lower())
        with self._lock:
            now = time.monotonic()
            self._recent(key, now)
            self._failures.setdefault(key, []).append(now)

    def reset(self, client: str | None = None, username: str | None = None) -> None:
        with self._lock:
            if client is None and username is None:
                self._failures.clear()
            else:
                self._failures.pop((client or "", (username or "").lower()), None)


login_throttle = LoginThrottle(
    max_failures=int(os.getenv("LOGIN_MAX_ATTEMPTS", "5")),
    window_seconds=int(os.getenv("LOGIN_WINDOW_SECONDS", "300")),
)


def authenticate(username: str, password: str) -> User | None:
    record = _USERS.get(username)
    if not record:
        # Equal-cost work reduces username enumeration timing differences.
        hashlib.pbkdf2_hmac("sha256", password.encode(), b"unknown-user", 200_000)
        return None
    role, salt_hex, expected = record
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000).hex()
    return User(username=username, role=role) if hmac.compare_digest(actual, expected) else None


def create_access_token(user: User, expires_minutes: int | None = None) -> str:
    now = datetime.now(UTC)
    minutes = _EXPIRES_MINUTES if expires_minutes is None else expires_minutes
    return jwt.encode(
        {"sub": user.username, "role": user.role.value, "iat": now, "exp": now + timedelta(minutes=minutes)},
        _SECRET,
        algorithm=_ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(credentials.credentials, _SECRET, algorithms=[_ALGORITHM])
        return User(username=claims["sub"], role=Role(claims["role"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[User], User]:
    allowed = set(roles) | {Role.admin}

    def dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            from app.database import log_security_event

            log_security_event(user.username, user.role.value, "authorization_denied", f"Required role: {', '.join(sorted(role.value for role in roles))}")
            raise HTTPException(403, f"Role '{user.role.value}' is not permitted for this action")
        return user

    return dependency
