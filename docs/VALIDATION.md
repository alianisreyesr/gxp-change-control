# Pydantic validation rules (API)

Portfolio prototype — educational data-quality gates, not a validated QMS.

## Global (`PortfolioModel`)

- `str_strip_whitespace=True`
- `extra="forbid"` (reject unknown fields)
- `use_enum_values=True`
- `validate_assignment=True`

## Actors (`requester`, `assessor`, `actor`)

- Pattern: starts with a letter; letters, digits, `.`, `_`, `-`
- **Rejected shared-style ids:** `admin`, `user`, `test`, `guest`, `root`, `system`, `shared`, `qa`, `it`, …
- Rationale: mirrors **attributable** expectations (ALCOA / Part 11 themes)

## `ChangeCreate`

| Field | Rules |
|-------|--------|
| title | 5–200 chars; not placeholder (`test`, `tbd`, `xxx`, …) |
| description | 20–4000 chars |
| priority high/critical | requires `business_justification` ≥ 15 chars |
| change_type / priority | Enums only |

## `ImpactAssessmentIn`

| Rule | Detail |
|------|--------|
| risk_summary | min 20 chars |
| residual_risk = high | risk_summary min 40 chars |
| ≥3 impact flags + residual_risk=low | risk_summary min 60 chars (must explain why residual stays low) |

## `ApprovalIn`

| Decision | Comment |
|----------|--------|
| approve | optional |
| reject / request_info | required, min 10 chars |

## Query params

- `status` on `GET /changes` → `Status` enum (422 if invalid)
- `actor` on submit/advance → same person-id rules as body fields

## Run tests

```bash
pip install -r requirements.txt
pytest tests/test_models.py -v
```
