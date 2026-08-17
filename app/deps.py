"""FastAPI dependencies that re-use Pydantic validation rules."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Path, Query
from pydantic import AfterValidator, TypeAdapter

from app.models import Status, _normalize_person, _validate_change_id_str

# TypeAdapters so FastAPI path/query validation shares model rules exactly.
_change_id_adapter = TypeAdapter(str)


def _parse_change_id(value: str) -> str:
    return _validate_change_id_str(value)


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
    Optional[Status],
    Query(
        description="Optional workflow status filter",
        examples=["pending_approval"],
    ),
]
