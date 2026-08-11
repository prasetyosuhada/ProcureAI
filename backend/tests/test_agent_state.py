import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from app.agent.state import (
    GraphState,
    RequirementDraftSchema,
    DemandAnalysisSchema,
    PRDraftSchema,
    create_initial_graph_state,
)

def test_requirement_draft_schema():
    """Verify RequirementDraftSchema default values and serialization."""
    draft = RequirementDraftSchema(
        category="IT Equipment",
        item="Laptop",
        quantity=10,
        purpose="Backend Engineering",
        required_date="2026-09-01",
        specifications={"ram": "32GB", "storage": "1TB SSD"}
    )
    assert draft.is_complete is False
    data = draft.model_dump()
    assert data["item"] == "Laptop"
    assert data["quantity"] == 10
    assert data["specifications"]["ram"] == "32GB"

def test_demand_analysis_schema():
    """Verify DemandAnalysisSchema structure."""
    analysis = DemandAnalysisSchema(
        requested_quantity=10,
        available_inventory=3,
        available_assets=2,
        recommended_quantity=5,
        justification="5 existing units satisfy partial demand.",
        is_complete=True
    )
    assert analysis.is_complete is True
    assert analysis.recommended_quantity == 5

def test_pr_draft_schema():
    """Verify PRDraftSchema structure."""
    pr = PRDraftSchema(
        pr_number="PR-2026-0001",
        category="IT Equipment",
        item="Laptop",
        quantity=5,
        specifications={"ram": "32GB"},
        purpose="Backend Team",
        required_date="2026-09-01",
        business_justification="Required for new backend engineers",
        demand_analysis_summary="Recommend 5 units based on 5 available assets"
    )
    assert pr.pr_number == "PR-2026-0001"
    assert pr.quantity == 5

def test_create_initial_graph_state():
    """Verify create_initial_graph_state helper function."""
    user_context = {
        "user_id": "usr_101",
        "department_id": "DEPT-ENG",
        "cost_center": "CC-ENG-001"
    }
    state: GraphState = create_initial_graph_state(user_context)
    assert state["messages"] == []
    assert state["user_context"]["user_id"] == "usr_101"
    assert state["requirement_draft"]["is_complete"] is False
    assert state["demand_analysis"]["is_complete"] is False
    assert state["pr_draft"] is None
    assert state["next_agent"] == "Clarification"

def test_add_messages_reducer():
    """Verify LangGraph add_messages reducer appends message sequences."""
    initial_messages = [HumanMessage(content="I need laptops")]
    new_messages = [AIMessage(content="How many laptops do you need?")]
    
    combined = add_messages(initial_messages, new_messages)
    assert len(combined) == 2
    assert combined[0].content == "I need laptops"
    assert combined[1].content == "How many laptops do you need?"
