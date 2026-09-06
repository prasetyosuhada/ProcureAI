import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.agent.state import RecommendationStatus, RequestOutcome, ResolutionProvenance

class RecommendationModificationSchema(BaseModel):
    net_new_purchase: Optional[int] = Field(
        default=None, 
        ge=0,
        description="Manually adjusted purchase quantity overriding AI recommendation (must be >= 0)"
    )
    user_notes: Optional[str] = Field(
        default=None, 
        description="Business justification / user notes for manual adjustment"
    )

    model_config = ConfigDict(extra="ignore")


class RecommendationActionRequest(BaseModel):
    action: Literal["accept", "keep_original", "modify", "reject"] = Field(
        ..., 
        description="Decision on AI demand recommendation: 'accept', 'keep_original', 'modify', or 'reject'"
    )
    modification: Optional[RecommendationModificationSchema] = Field(
        default=None,
        description="Modification details (required when action='modify')"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "modify",
                "modification": {
                    "net_new_purchase": 8,
                    "user_notes": "Adding 2 buffer units for incoming Q3 contractors"
                }
            }
        }
    )


class ConfirmSpecificationsResponse(BaseModel):
    thread_id: str
    is_confirmed: bool
    message: str
    next_agent: str
    pr: Dict[str, Any]
    progress: Dict[str, Any]
    attention_items: List[Dict[str, Any]]


class ResolveAttentionResponse(BaseModel):
    thread_id: str
    resolved_item_id: str
    message: str
    attention_items: List[Dict[str, Any]]
    blocking_count: int


class SubmitPRRequest(BaseModel):
    notes: Optional[str] = Field(default=None, description="Optional submitter comments")


class SubmitPRResponse(BaseModel):
    thread_id: str
    pr_number: str
    status: str
    submitted_at: str
    message: str
    pr: Dict[str, Any]
    progress: Dict[str, Any]
    request_outcome: RequestOutcome


class ResolveWithoutPurchaseResponse(BaseModel):
    thread_id: str
    request_outcome: Literal["resolved_without_purchase"]
    resolution_provenance: ResolutionProvenance
    resolution_reason: str
    resolved_at: str
    message: str
    recommendation_status: RecommendationStatus
    pr: Dict[str, Any]
    demand: Dict[str, Any]
    progress: Dict[str, Any]


class RequestStateResponse(BaseModel):
    thread_id: str
    pr: Dict[str, Any]
    progress: Dict[str, Any]
    demand: Optional[Dict[str, Any]] = None
    agent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    attention_items: List[Dict[str, Any]] = Field(default_factory=list)
    recommendation_status: RecommendationStatus = "none"
    request_outcome: RequestOutcome = "open"
    resolution_provenance: Optional[ResolutionProvenance] = None
    resolution_reason: Optional[str] = None
    resolved_at: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    last_message: Optional[str] = None
    next_agent: str = "Clarification"
