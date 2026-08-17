# Date / date-time format validation

## Rules

| Kind | Format | Notes |
|------|--------|--------|
| **date** | `YYYY-MM-DD` | Calendar date only (`format: date`) |
| **date-time** | ISO 8601 with **timezone** | `...Z` or `±hh:mm` required — naive stamps rejected |

Server timestamps (`created_at`, `updated_at`, `assessed_at`, `decided_at`) are always **UTC ISO** via `utc_now_iso()`.

### Input field

`target_implementation_date` on `ChangeCreate`:

- Optional
- Must be `YYYY-MM-DD`
- Must **not** be in the past (UTC “today”)

## Layers

1. **Pydantic** — `IsoDate` / `IsoDateTime` + `app/datetime_validation.py`  
2. **JSON Schema** — `format: date` / `format: date-time`  
3. **Ajv** — `ajv-formats` validates those formats client-side  

## Why timezone-aware?

For audit-oriented logs, a naive local timestamp is ambiguous. Requiring offset/`Z` mirrors **contemporaneous / attributable** record practices in educational GxP demos (not a claim of Part 11 compliance).
