"""JSON Schema registry built from Pydantic v2 models (source of truth)."""

from __future__ import annotations

from typing import Any

from app.models import (
    ApprovalIn,
    ApprovalOut,
    ActivityOut,
    ChangeCreate,
    ChangeOut,
    HealthOut,
    ImpactAssessmentIn,
    ImpactAssessmentOut,
    ValidationErrorBody,
)

# Draft dialect used by Pydantic v2 model_json_schema by default in recent versions.
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# Public names → model class
MODEL_MAP: dict[str, type] = {
    "change-create": ChangeCreate,
    "change-out": ChangeOut,
    "impact-assessment-in": ImpactAssessmentIn,
    "impact-assessment-out": ImpactAssessmentOut,
    "approval-in": ApprovalIn,
    "approval-out": ApprovalOut,
    "activity-out": ActivityOut,
    "health-out": HealthOut,
    "validation-error": ValidationErrorBody,
}


def build_schema(name: str) -> dict[str, Any]:
    if name not in MODEL_MAP:
        raise KeyError(name)
    model = MODEL_MAP[name]
    # Validation mode for both inputs and outputs: outputs are still fine
    # documented this way, and inputs need validation-mode constraints.
    schema = model.model_json_schema(mode="validation")
    schema["$id"] = f"https://alianisreyesr.github.io/gxp-change-control/schemas/{name}.json"
    schema["$schema"] = SCHEMA_DIALECT
    schema["title"] = schema.get("title") or name
    schema["description"] = (
        schema.get("description")
        or f"JSON Schema for {model.__name__} (generated from Pydantic). Portfolio synthetic API only."
    )
    return schema


def list_schema_names() -> list[str]:
    return sorted(MODEL_MAP.keys())


def build_all() -> dict[str, dict[str, Any]]:
    return {name: build_schema(name) for name in list_schema_names()}
