"""JSON Schema generation and HTTP exposure."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas_registry import build_schema, list_schema_names

client = TestClient(app)
ROOT = Path(__file__).resolve().parent.parent


def test_registry_lists_core_schemas():
    names = list_schema_names()
    assert "change-create" in names
    assert "approval-in" in names


def test_build_change_create_schema_has_required_and_enums():
    schema = build_schema("change-create")
    assert schema["type"] == "object"
    assert "title" in schema["properties"]
    assert set(schema["required"]) >= {"title", "description", "system_name", "change_type", "requester"}
    # change_type should surface as enum via $defs or inline
    dumped = json.dumps(schema)
    assert "configuration" in dumped
    assert schema.get("$schema")


def test_schemas_catalog_endpoint():
    r = client.get("/schemas")
    assert r.status_code == 200
    body = r.json()
    assert "schemas" in body
    assert any(s["name"] == "change-create" for s in body["schemas"])


def test_schemas_detail_endpoint():
    r = client.get("/schemas/change-create")
    assert r.status_code == 200
    assert r.json()["title"] in ("ChangeCreate", "change-create") or "properties" in r.json()


def test_schemas_unknown_404():
    r = client.get("/schemas/does-not-exist")
    assert r.status_code == 404


def test_static_schema_files_exist():
    assert (ROOT / "schemas" / "change-create.json").is_file()
    assert (ROOT / "schemas" / "approval-in.json").is_file()
