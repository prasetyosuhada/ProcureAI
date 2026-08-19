import pytest
from langchain_core.messages import HumanMessage
from app.agent.state import create_initial_graph_state
from app.agent.nodes.clarification_node import requirement_clarification_node, extract_requirement_heuristics

def test_extract_requirement_heuristics_incomplete():
    """Verify extraction on incomplete user request."""
    user_text = "I need laptops for my team"
    draft = extract_requirement_heuristics(user_text, {})
    assert draft["item"] == "Laptop"
    assert draft["quantity"] is None
    assert draft["is_complete"] is False

def test_extract_requirement_heuristics_complete():
    """Verify extraction on complete user request."""
    user_text = "I need 10 laptops for backend development before Sept 1 with 32GB RAM and 1TB SSD"
    draft = extract_requirement_heuristics(user_text, {})
    assert draft["item"] == "Laptop"
    assert draft["quantity"] == 10
    assert draft["purpose"] == "Backend Development Team"
    assert draft["required_date"] == "2026-09-01"
    assert draft["specifications"]["ram"] == "32GB"
    assert draft["specifications"]["storage"] == "1TB SSD"
    assert draft["is_complete"] is True

@pytest.mark.asyncio
async def test_clarification_node_incomplete():
    """Verify requirement_clarification_node response when requirement is incomplete."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [HumanMessage(content="We need monitors for design team")]
    
    result = await requirement_clarification_node(state)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["next_agent"] == "Clarification"
    assert result["requirement_draft"]["is_complete"] is False

@pytest.mark.asyncio
async def test_clarification_node_complete():
    """Verify requirement_clarification_node response when requirement details are complete (pending user confirmation)."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [
        HumanMessage(content="I need 10 laptops for backend development before September 1")
    ]
    
    result = await requirement_clarification_node(state)
    assert result["next_agent"] == "Clarification"
    assert result["requirement_draft"]["is_complete"] is True
    assert result["requirement_draft"]["quantity"] == 10
    assert "confirm" in result["messages"][0].content.lower() or "summary" in result["messages"][0].content.lower() or "demand" in result["messages"][0].content.lower()

@pytest.mark.asyncio
async def test_clarification_node_other_item():
    """Verify requirement_clarification_node handles arbitrary items like standing desks."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [
        HumanMessage(content="I need 5 standing desks for UI/UX Design Team before Sept 1")
    ]
    
    result = await requirement_clarification_node(state)
    assert result["next_agent"] == "Clarification"
    assert result["requirement_draft"]["is_complete"] is True
    assert result["requirement_draft"]["item"] == "Standing Desks" or result["requirement_draft"]["item"] == "Standing Desk"
    assert result["requirement_draft"]["quantity"] == 5
    assert result["requirement_draft"]["category"] == "Office Furniture > Desks"
