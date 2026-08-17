"""FastAPI dependencies that re-use Pydantic validation rules."""

from __future__ import annotations

from typing import Annotated

from fastapi import Path, Query
from pydantic import AfterValidator, ValidationError

from app.models import ActorQuery, ChangeIdStr, Status, _normalize_person


def _parse_change_id(value: str) -> str:
    """Validate path param using the same ChangeIdStr rules."""
    try:
        return ChangeIdStr(value)
    except ValidationError as exc:
        # Re-raise so FastAPI turns it into a 422 with detail
        raise ValueError(exc.errors()[0]["msg"]) from exc


def _parse_actor(value: str) -> str:
    return _normalize_person(value)


ChangeIdPath = Annotated[
    str,
    Path(
        description="Change identifier (CHG-XXXX)",
        examples=["CHG-1001"],
        min_length=8,
        max_length=20,
        pattern=r"^CHG-[A-Z0-9]{4,12}$",
    ),
    AfterValidator(_parse_change_id),
]

ActorParam = Annotated[
    str,
    Query(
        description="Attributable person identifier (not shared accounts)",
        examples=["a.reyes"],
        min_length=2,
        max_length=80,
    ),
    AfterValidator(_parse_actor),
]

StatusFilter = Annotated[
    Status | None,
    Query(
        description="Optional workflow status filter",
        examples=["pending_approval"],
    ),
]


def get_actor_query(actor: ActorParam) -> str:
    """Dependency-style accessor (already validated)."""
    return ActorQuery(actor=actor).actor
