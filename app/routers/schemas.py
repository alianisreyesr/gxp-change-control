"""Serve JSON Schema documents for client-side / offline validation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas_registry import build_all, build_schema, list_schema_names

router = APIRouter(prefix="/schemas", tags=["json-schema"])


@router.get("")
def list_schemas():
    """Catalog of available JSON Schemas (derived from Pydantic models)."""
    return {
        "dialect": "https://json-schema.org/draft/2020-12/schema",
        "source_of_truth": "Pydantic v2 models in app.models",
        "schemas": [
            {"name": n, "path": f"/schemas/{n}"} for n in list_schema_names()
        ],
    }


@router.get("/{name}")
def get_schema(name: str):
    """Return a single JSON Schema document."""
    try:
        schema = build_schema(name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown schema '{name}'. See GET /schemas for the catalog.",
        )
    return JSONResponse(
        content=schema,
        media_type="application/schema+json",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/export/all")
def export_all():
    """Bundle all schemas (useful for codegen or offline packs)."""
    return build_all()
