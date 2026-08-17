#!/usr/bin/env python3
"""Write JSON Schema files under schemas/ (CI / docs artifact)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.schemas_registry import build_all  # noqa: E402

OUT = ROOT / "schemas"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_schemas = build_all()
    index = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "GxP Change Control — schema index",
        "description": "Generated from Pydantic models. Portfolio only.",
        "schemas": {},
    }
    for name, schema in all_schemas.items():
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        index["schemas"][name] = f"{name}.json"
        print(f"wrote {path.relative_to(ROOT)}")
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"wrote schemas/index.json ({len(all_schemas)} schemas)")


if __name__ == "__main__":
    main()
