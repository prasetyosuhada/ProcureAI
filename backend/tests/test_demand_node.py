import pytest
from langchain_core.messages import HumanMessage
from app.agent.state import create_initial_graph_state
from app.agent.nodes.demand_node import demand_analysis_node

@pytest.mark.asyncio
async def test_demand_node_partial_stock_deduction():
    """Test demand_node when existing stock partially covers requested quantity."""
    state = create_initial_graph_state({"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"})
    state["requirement_draft"] = {
        "item": "Laptop",
        "category": "IT Equipment > Laptops",
        "quantity": 10,
        "purpose": "Backend Team",
        "required_date": "2026-09-01",
        "is_complete": True
    }
    
    result = await demand_analysis_node(state)
    assert result["next_agent"] == "GeneratePR"
    demand = result["demand_analysis"]
    assert demand["is_complete"] is True
    assert demand["requested_quantity"] == 10
    assert demand["available_inventory"] == 3
    assert demand["available_assets"] == 5
    assert demand["recommended_quantity"] == 2  # 10 - (3 + 5) = 2
    assert "recommended new purchase quantity is 2" in demand["justification"]

@pytest.mark.asyncio
async def test_demand_node_full_internal_fulfillment():
    """Test demand_node when existing stock completely covers requested quantity."""
    state = create_initial_graph_state({"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"})
    state["requirement_draft"] = {
        "item": "Laptop",
        "category": "IT Equipment > Laptops",
        "quantity": 4,
        "purpose": "Backend Team",
        "required_date": "2026-09-01",
        "is_complete": True
    }
    
    result = await demand_analysis_node(state)
    assert result["next_agent"] == "GeneratePR"
    demand = result["demand_analysis"]
    assert demand["recommended_quantity"] == 0  # 4 <= (3 + 5)
    assert "Recommended new purchase quantity is 0" in demand["justification"]

@pytest.mark.asyncio
async def test_demand_node_no_stock():
    """Test demand_node when no existing inventory or assets are found."""
    state = create_initial_graph_state({"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"})
    state["requirement_draft"] = {
        "item": "Ergonomic Keyboard Special",
        "category": "IT Supplies",
        "quantity": 2,
        "purpose": "Engineering Team",
        "required_date": "2026-09-01",
        "is_complete": True
    }
    
    result = await demand_analysis_node(state)
    assert result["next_agent"] == "GeneratePR"
    demand = result["demand_analysis"]
    assert demand["recommended_quantity"] == 2
    assert demand["available_inventory"] == 0
    assert demand["available_assets"] == 0
    assert "No existing warehouse stock" in demand["justification"]
