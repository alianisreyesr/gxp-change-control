# Pydantic ↔ FastAPI integration

Portfolio prototype — educational validation gates, not a validated QMS.

## How validation is wired

| Layer | Mechanism |
|-------|-----------|
| **JSON body** | FastAPI injects `ChangeCreate`, `ImpactAssessmentIn`, `ApprovalIn` → Pydantic v2 |
| **Path** | `ChangeIdPath` (`Annotated` + pattern + `AfterValidator`) |
| **Query** | `ActorParam`, `StatusFilter` (`Annotated` + validators) |
| **Response** | `response_model=…` serializes with the same schemas |
| **Errors** | Custom `RequestValidationError` handler → stable **422** JSON |

### 422 response shape

```json
{
  "error": "validation_error",
  "message": "Request failed Pydantic / FastAPI validation",
  "details": [
    { "loc": ["body", "requester"], "msg": "...", "type": "value_error" }
  ]
}
```

OpenAPI documents bodies and enums automatically at `/docs`.

## Domain rules (summary)

- **Actors:** unique person ids; shared names (`admin`, `user`, …) rejected  
- **ChangeCreate:** title quality, description length, high/critical → justification  
- **ImpactAssessmentIn:** residual risk vs summary length / impact flags  
- **ApprovalIn:** reject / request_info require comment  
- **extra="forbid":** unknown JSON fields → 422  

## Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
