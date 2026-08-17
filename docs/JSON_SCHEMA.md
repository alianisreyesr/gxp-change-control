# JSON Schema validation

## Source of truth

| Layer | Role |
|-------|------|
| **Pydantic v2 models** (`app/models.py`) | Runtime validation for FastAPI (including cross-field rules JSON Schema cannot fully express alone) |
| **JSON Schema** | Portable contract for clients, codegen, and documentation |

Pydantic **generates** JSON Schema; FastAPI embeds it in **OpenAPI** at `/docs`.

## HTTP endpoints

```http
GET /schemas                 # catalog
GET /schemas/{name}          # one document (application/schema+json)
GET /schemas/export/all      # full bundle
```

Examples: `change-create`, `impact-assessment-in`, `approval-in`, `change-out`, `validation-error`.

## Static files

Checked-in samples under `schemas/`:

- `change-create.json` — enums, required, `additionalProperties: false`
- `impact-assessment-in.json` — `if/then` for high residual risk length
- `approval-in.json` — `if/then` requiring comment on reject / request_info
- `index.json` — catalog

Regenerate from models:

```bash
python scripts/export_json_schemas.py
```

## What JSON Schema covers vs Pydantic

| Rule | JSON Schema | Pydantic runtime |
|------|-------------|------------------|
| types, enums, minLength | ✅ | ✅ |
| additionalProperties: false | ✅ | ✅ (`extra="forbid"`) |
| reject/request_info → comment | ✅ (`if`/`then`) | ✅ |
| residual_risk=high → longer summary | ✅ partial | ✅ |
| forbidden actors (`admin`, …) | ❌ (custom) | ✅ |
| high priority → justification | ❌ / hard | ✅ `model_validator` |
| ≥3 impact flags + low residual | ❌ / hard | ✅ |

**Design choice:** keep complex GxP-oriented rules in Pydantic; publish JSON Schema for structure, enums, and the rules that map cleanly to Draft 2020-12.

## Client-side validation (optional)

```bash
npm install ajv
# fetch GET /schemas/change-create and compile with Ajv
```

Or validate offline against files in `schemas/`.

## OpenAPI

FastAPI already exposes the same shapes under the request/response schemas in `/openapi.json` — JSON Schema and OpenAPI stay aligned because both derive from Pydantic.
