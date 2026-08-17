"""Metadata endpoints: timezone policy, health-adjacent info."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.datetime_validation import (
    convert_local_iso_to_utc,
    timezone_policy_info,
    validate_iana_zone,
)
from app.models import PortfolioModel

router = APIRouter(prefix="/meta", tags=["meta"])


class LocalToUtcIn(PortfolioModel):
    local_iso: str = Field(
        description="Naive local wall time ISO, e.g. 2026-08-17T08:00:00",
        examples=["2026-08-17T08:00:00"],
    )
    iana_zone: str = Field(
        description="IANA time zone id",
        examples=["America/Puerto_Rico", "UTC", "America/New_York"],
    )


class LocalToUtcOut(PortfolioModel):
    utc_iso: str
    iana_zone: str
    policy: str


@router.get("/timezone-policy")
def get_timezone_policy():
    """Document API timezone acceptance rules (portfolio)."""
    return timezone_policy_info()


@router.get("/timezone/{zone_name:path}")
def check_zone(zone_name: str):
    """Validate an IANA zone id exists on this runtime."""
    try:
        zi = validate_iana_zone(zone_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"iana": zone_name, "key": getattr(zi, "key", str(zi)), "valid": True}


@router.post("/timezone/to-utc", response_model=LocalToUtcOut)
def local_to_utc(body: LocalToUtcIn):
    """
    Demo: convert naive local wall time + IANA zone → UTC ISO.

    Primary change-control stamps still require aware ISO on the wire;
    this endpoint teaches why zone context matters.
    """
    try:
        utc_iso = convert_local_iso_to_utc(body.local_iso, body.iana_zone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LocalToUtcOut(
        utc_iso=utc_iso,
        iana_zone=body.iana_zone,
        policy=timezone_policy_info()["policy"],
    )
