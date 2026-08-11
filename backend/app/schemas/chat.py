import datetime
import uuid
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"] = Field(..., description="Sender role")
    content: str = Field(..., description="Message text content")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat(),
        description="ISO timestamp of message"
    )

class ChatRequest(BaseModel):
    thread_id: Optional[str] = Field(
        default=None,
        description="Conversational thread ID. Generated if not provided."
    )
    message: str = Field(..., min_length=1, description="Natural language user input")
    requirement_override: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User override of structured requirement draft"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "thread_id": "thread_abc123",
                "message": "I need 10 laptops for new backend developers joining next month."
            }
        }
    )

class ChatResponse(BaseModel):
    thread_id: str = Field(..., description="Unique conversation thread ID")
    message: ChatMessage = Field(..., description="Latest agent response message")
    requirement_draft: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current structured requirement draft"
    )
    demand_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Demand analysis and quantity recommendation"
    )
    pr_draft: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Final generated Purchase Requisition draft"
    )
    next_agent: str = Field(
        default="Clarification",
        description="Current workflow phase: Clarification | Demand | PRDraft | Complete"
    )
