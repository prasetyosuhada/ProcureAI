from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ConfigDict

class RequirementDraftSchema(BaseModel):
    category: Optional[str] = Field(default=None, description="Procurement category, e.g., 'IT Equipment > Laptops'")
    item: Optional[str] = Field(default=None, description="Requested item name, e.g., 'Laptop'")
    quantity: Optional[int] = Field(default=None, description="Requested quantity")
    purpose: Optional[str] = Field(default=None, description="Business purpose or team role")
    required_date: Optional[str] = Field(default=None, description="Target delivery/required date (YYYY-MM-DD)")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Technical specifications like RAM, storage")
    is_complete: bool = Field(default=False, description="True if all mandatory fields are extracted and confirmed")

    model_config = ConfigDict(extra="ignore")

class DemandAnalysisSchema(BaseModel):
    requested_quantity: Optional[int] = Field(default=None, description="Initial quantity requested by user")
    available_inventory: int = Field(default=0, description="Warehouse stock quantity found")
    available_assets: int = Field(default=0, description="Unused or returning assets count")
    recommended_quantity: Optional[int] = Field(default=None, description="Data-backed recommended new purchase quantity")
    justification: Optional[str] = Field(default=None, description="Natural language explanation of the recommendation")
    is_complete: bool = Field(default=False, description="True if demand analysis and recommendation are complete")

    model_config = ConfigDict(extra="ignore")

class PRDraftSchema(BaseModel):
    pr_number: str = Field(..., description="Unique generated Purchase Requisition number")
    category: str = Field(..., description="Item category")
    item: str = Field(..., description="Item name")
    quantity: int = Field(..., description="Final purchase quantity")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Item specifications")
    purpose: str = Field(..., description="Business purpose")
    required_date: str = Field(..., description="Required date")
    business_justification: str = Field(..., description="Justification statement")
    demand_analysis_summary: str = Field(..., description="Summary of demand analysis reasoning")

    model_config = ConfigDict(extra="ignore")

class GraphState(TypedDict):
    """
    Global LangGraph State passed between nodes (Orchestrator, Clarification Agent, Demand Agent).
    Uses add_messages reducer for message history concatenation.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_context: Dict[str, Any]
    requirement_draft: Dict[str, Any]
    demand_analysis: Dict[str, Any]
    pr_draft: Optional[Dict[str, Any]]
    next_agent: Literal["Clarification", "Demand", "GeneratePR", "End"]

def create_initial_graph_state(user_context_dict: Dict[str, Any]) -> GraphState:
    """Helper function to create a blank initial GraphState for a thread."""
    return {
        "messages": [],
        "user_context": user_context_dict,
        "requirement_draft": RequirementDraftSchema().model_dump(),
        "demand_analysis": DemandAnalysisSchema().model_dump(),
        "pr_draft": None,
        "next_agent": "Clarification"
    }
