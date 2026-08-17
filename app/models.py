from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

ChangeType = Literal["configuration", "code", "process", "infrastructure", "documentation"]
Priority = Literal["low", "medium", "high", "critical"]
Status = Literal[
    "draft",
    "submitted",
    "impact_assessment",
    "pending_approval",
    "approved",
    "rejected",
    "implementing",
    "verification",
    "closed",
    "cancelled",
]
ResidualRisk = Literal["low", "medium", "high"]


class ChangeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=4000)
    system_name: str = Field(min_length=2, max_length=200)
    change_type: ChangeType
    priority: Priority = "medium"
    requester: str = Field(min_length=2, max_length=100)
    business_justification: Optional[str] = Field(default=None, max_length=2000)


class ChangeOut(BaseModel):
    id: str
    title: str
    description: str
    system_name: str
    change_type: ChangeType
    priority: Priority
    status: Status
    requester: str
    business_justification: Optional[str]
    created_at: str
    updated_at: str


class ImpactAssessmentIn(BaseModel):
    affects_validated_state: bool = False
    affects_part11_controls: bool = False
    affects_data_integrity: bool = False
    affects_training: bool = False
    affects_sops: bool = False
    risk_summary: str = Field(min_length=5, max_length=4000)
    residual_risk: ResidualRisk = "low"
    assessor: str = Field(min_length=2, max_length=100)


class ImpactAssessmentOut(ImpactAssessmentIn):
    id: str
    change_id: str
    assessed_at: Optional[str]


class ApprovalIn(BaseModel):
    role: str = Field(min_length=2, max_length=80)
    decision: Literal["approve", "reject", "request_info"]
    comment: Optional[str] = Field(default=None, max_length=2000)
    actor: str = Field(min_length=2, max_length=100)


class ApprovalOut(ApprovalIn):
    id: str
    change_id: str
    decided_at: str


class ActivityOut(BaseModel):
    id: int
    change_id: str
    actor: str
    action: str
    detail: Optional[str]
    created_at: str


class HealthOut(BaseModel):
    status: str
    service: str
    data_classification: str
    version: str
