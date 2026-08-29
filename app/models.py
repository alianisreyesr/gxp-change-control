from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.datetime_validation import (
    assert_target_not_in_past,
    ensure_iso_date_str,
    ensure_iso_datetime_str,
    parse_iso_date,
)


class ChangeType(str, Enum):
    configuration = "configuration"
    code = "code"
    process = "process"
    infrastructure = "infrastructure"
    documentation = "documentation"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Status(str, Enum):
    draft = "draft"
    impact_assessment = "impact_assessment"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    implementing = "implementing"
    verification = "verification"
    closed = "closed"


class ResidualRisk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Decision(str, Enum):
    approve = "approve"
    reject = "reject"
    request_info = "request_info"


_FORBIDDEN_ACTORS = {
    "admin",
    "administrator",
    "user",
    "test",
    "guest",
    "root",
    "system",
    "shared",
    "qa",
    "it",
}

_ACTOR_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9._\-]{1,79}$")
_CHANGE_ID_RE = re.compile(r"^CHG-[A-Z0-9]{4,12}$")


def _normalize_person(value: str) -> str:
    cleaned = " ".join(value.split()).strip()
    if not cleaned:
        raise ValueError("must not be empty or whitespace-only")
    if cleaned.lower() in _FORBIDDEN_ACTORS:
        raise ValueError(
            f"'{cleaned}' is not allowed as an attributable actor; "
            "use a unique person identifier (e.g. a.reyes)"
        )
    if not _ACTOR_RE.match(cleaned):
        raise ValueError(
            "must start with a letter and contain only letters, digits, '.', '_' or '-'"
        )
    return cleaned


def _validate_change_id_str(value: str) -> str:
    value = value.strip().upper()
    if not _CHANGE_ID_RE.match(value):
        raise ValueError("must match pattern CHG-[A-Z0-9]{4,12} (e.g. CHG-1001)")
    return value


ChangeIdStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=8, max_length=20),
    AfterValidator(_validate_change_id_str),
]

PersonId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=80),
    AfterValidator(_normalize_person),
]

# JSON Schema: format date / date-time (Ajv + OpenAPI)
IsoDate = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    AfterValidator(ensure_iso_date_str),
    Field(json_schema_extra={"format": "date", "examples": ["2026-09-01"]}),
]

IsoDateTime = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=20, max_length=40),
    AfterValidator(ensure_iso_datetime_str),
    Field(
        json_schema_extra={
            "format": "date-time",
            "examples": ["2026-08-17T12:00:00+00:00", "2026-08-17T12:00:00Z"],
        }
    ),
]


class PortfolioModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        use_enum_values=True,
        validate_assignment=True,
    )


class ChangeCreate(PortfolioModel):
    title: str = Field(
        min_length=5,
        max_length=200,
        description="Short, specific change title",
        examples=["Update audit-log retention label in UI"],
    )
    description: str = Field(
        min_length=20,
        max_length=4000,
        description="What will change and what will not",
    )
    system_name: str = Field(min_length=2, max_length=200)
    change_type: ChangeType
    priority: Priority = Priority.medium
    requester: PersonId
    business_justification: Optional[str] = Field(default=None, max_length=2000)
    target_implementation_date: Optional[IsoDate] = Field(
        default=None,
        description="Planned implementation calendar date (YYYY-MM-DD, not in the past)",
    )

    @field_validator("title", "description", "system_name", "business_justification", mode="before")
    @classmethod
    def empty_to_none_or_strip(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v

    @field_validator("title")
    @classmethod
    def title_not_placeholder(cls, v: str) -> str:
        lowered = v.lower()
        banned = ("test", "asdf", "xxx", "tbd", "n/a", "todo")
        if lowered in banned or all(ch == lowered[0] for ch in lowered if ch.isalnum()):
            raise ValueError("title looks like a placeholder; provide a meaningful title")
        return v

    @field_validator("target_implementation_date", mode="before")
    @classmethod
    def empty_date_to_none(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @model_validator(mode="after")
    def priority_and_dates(self):
        if self.priority in (Priority.high, Priority.critical, "high", "critical"):
            if not self.business_justification or len(self.business_justification.strip()) < 15:
                raise ValueError(
                    "business_justification (min 15 chars) is required when priority is high or critical"
                )
        if self.target_implementation_date:
            d = parse_iso_date(self.target_implementation_date)
            assert_target_not_in_past(d)
        return self


class ChangeOut(PortfolioModel):
    id: ChangeIdStr
    title: str
    description: str
    system_name: str
    change_type: ChangeType
    priority: Priority
    status: Status
    requester: str
    business_justification: Optional[str] = None
    target_implementation_date: Optional[str] = Field(
        default=None,
        json_schema_extra={"format": "date"},
    )
    created_at: IsoDateTime
    updated_at: IsoDateTime

    @field_validator("target_implementation_date", mode="before")
    @classmethod
    def optional_date(cls, v):
        if v is None or v == "":
            return None
        return ensure_iso_date_str(str(v))


class ImpactAssessmentIn(PortfolioModel):
    affects_validated_state: bool = False
    affects_part11_controls: bool = False
    affects_data_integrity: bool = False
    affects_training: bool = False
    affects_sops: bool = False
    risk_summary: str = Field(min_length=20, max_length=4000)
    residual_risk: ResidualRisk = ResidualRisk.low
    assessor: PersonId

    @model_validator(mode="after")
    def residual_risk_consistency(self):
        flags = [
            self.affects_validated_state,
            self.affects_part11_controls,
            self.affects_data_integrity,
            self.affects_training,
            self.affects_sops,
        ]
        hit_count = sum(1 for f in flags if f)

        if self.residual_risk in (ResidualRisk.high, "high") and len(self.risk_summary) < 40:
            raise ValueError("risk_summary must be at least 40 characters when residual_risk is high")

        if hit_count >= 3 and self.residual_risk in (ResidualRisk.low, "low"):
            if len(self.risk_summary) < 60:
                raise ValueError(
                    "when three or more impact flags are true, residual_risk=low requires "
                    "a detailed risk_summary (min 60 chars) explaining why residual risk remains low"
                )
        return self


class ImpactAssessmentOut(ImpactAssessmentIn):
    id: str
    change_id: ChangeIdStr
    assessed_at: Optional[IsoDateTime] = None


class ApprovalIn(PortfolioModel):
    role: str = Field(min_length=2, max_length=80)
    decision: Decision
    comment: Optional[str] = Field(default=None, max_length=2000)
    actor: PersonId

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("role is required")
        return v

    @model_validator(mode="after")
    def decision_comment_rules(self):
        decision = self.decision.value if isinstance(self.decision, Decision) else self.decision
        if decision in ("reject", "request_info"):
            if not self.comment or len(self.comment.strip()) < 10:
                raise ValueError(
                    f"comment (min 10 chars) is required when decision is '{decision}'"
                )
        return self


class ApprovalOut(ApprovalIn):
    id: str
    change_id: ChangeIdStr
    decided_at: IsoDateTime


class ActivityOut(PortfolioModel):
    id: int = Field(ge=1)
    change_id: str
    actor: str
    action: str = Field(min_length=1, max_length=120)
    detail: Optional[str] = None
    created_at: IsoDateTime


class ActorQuery(PortfolioModel):
    actor: PersonId


class ErrorDetail(PortfolioModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorBody(PortfolioModel):
    error: str = "validation_error"
    message: str = "Request failed Pydantic / FastAPI validation"
    details: list[ErrorDetail]


class HealthOut(PortfolioModel):
    status: str
    service: str
    data_classification: str
    version: str
