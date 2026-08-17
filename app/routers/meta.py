"""Metadata endpoints: timezone policy, DST fold analysis."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import Field

from app.datetime_validation import (
    analyze_wall_time,
    convert_local_iso_to_utc,
    timezone_policy_info,
    validate_iana_zone,
)
from app.models import PortfolioModel

router = APIRouter(prefix="/meta", tags=["meta"])


class LocalToUtcIn(PortfolioModel):
    local_iso: str = Field(
        description="Naive local wall time ISO (no offset)",
        examples=["2025-11-02T01:30:00", "2026-08-17T08:00:00"],
    )
    iana_zone: str = Field(
        description="IANA time zone id",
        examples=["America/New_York", "America/Puerto_Rico", "UTC"],
    )
    fold: Optional[Literal[0, 1]] = Field(
        default=None,
        description="Required when local time is DST-ambiguous: 0=first occurrence, 1=second",
    )


class LocalToUtcOut(PortfolioModel):
    utc_iso: str
    iana_zone: str
    fold_used: Optional[int] = None
    kind: str
    policy: str


class AnalyzeIn(PortfolioModel):
    local_iso: str = Field(examples=["2025-11-02T01:30:00"])
    iana_zone: str = Field(examples=["America/New_York"])


@router.get("/timezone-policy")
def get_timezone_policy():
    return timezone_policy_info()


@router.get("/timezone/{zone_name:path}")
def check_zone(zone_name: str):
    try:
        zi = validate_iana_zone(zone_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"iana": zone_name, "key": getattr(zi, "key", str(zi)), "valid": True}


@router.post("/timezone/analyze")
def analyze_local(body: AnalyzeIn):
    """
    Classify local wall time: unique | ambiguous | nonexistent (DST fold detection).
    """
    try:
        result = analyze_wall_time(body.local_iso, body.iana_zone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.to_dict()


@router.get("/timezone/analyze")
def analyze_local_get(
    local_iso: str = Query(..., examples=["2025-11-02T01:30:00"]),
    iana_zone: str = Query("America/New_York"),
):
    try:
        result = analyze_wall_time(local_iso, iana_zone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.to_dict()


@router.post("/timezone/to-utc", response_model=LocalToUtcOut)
def local_to_utc(body: LocalToUtcIn):
    """
    Convert naive local + IANA → UTC.

    If the local time is **ambiguous** (DST fall-back), pass ``fold`` 0 or 1.
    If **nonexistent** (DST gap), returns 422.
    """
    try:
        analysis = analyze_wall_time(body.local_iso, body.iana_zone)
        utc_iso = convert_local_iso_to_utc(
            body.local_iso, body.iana_zone, fold=body.fold
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    fold_used: Optional[int] = body.fold
    if fold_used is None and analysis.instants:
        fold_used = analysis.instants[0].fold

    return LocalToUtcOut(
        utc_iso=utc_iso,
        iana_zone=body.iana_zone,
        fold_used=fold_used,
        kind=analysis.kind.value,
        policy=timezone_policy_info()["policy"],
    )
