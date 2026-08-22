import pytest
from unittest.mock import patch
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


@pytest.mark.asyncio
async def test_demand_node_stale_override_protection():
    """
    Verify stale manual override detection:
    1. Run demand_analysis_node first time -> get initial net_new_purchase from normal calculation.
    2. Simulate manual override: set is_manually_overridden=True, net_new_purchase=8, save to state.
    3. Change underlying inventory (mock get_inventory returns 7 units instead of 3).
    4. Run demand_analysis_node again with state from step 2.
    5. Assert:
       - net_new_purchase in output remains 8 (protected).
       - is_manually_overridden remains True.
       - AttentionItem with id override_stale_cc-eng-001 is present in output.
    """
    user_context = {"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"}
    state = create_initial_graph_state(user_context)
    state["requirement_draft"] = {
        "item": "Laptop",
        "category": "IT Equipment > Laptops",
        "quantity": 10,
        "purpose": "Backend Team",
        "required_date": "2026-09-01",
        "is_complete": True
    }

    # Step 1: Initial calculation (requested=10, inv=3, assets=5 -> net_new_purchase=2)
    r1 = await demand_analysis_node(state)
    assert r1["demand"]["net_new_purchase"] == 2
    assert r1["demand"]["is_manually_overridden"] is False

    # Step 2: Simulate user manual override to 8
    state["demand"] = {
        **r1["demand"],
        "net_new_purchase": 8,
        "is_manually_overridden": True,
        "override_reason": "Need extra buffer for Q3 interns"
    }

    # Step 3 & 4: Inventory changes (from 3 to 7) and node is re-run
    with patch("app.agent.nodes.demand_node.get_inventory") as mock_inv:
        mock_inv.invoke.return_value = {
            "item_name": "Laptop",
            "available_quantity": 7,
            "unit": "units"
        }
        r2 = await demand_analysis_node(state)

    # Step 5: Assertions
    assert r2["demand"]["net_new_purchase"] == 8
    assert r2["demand"]["is_manually_overridden"] is True
    assert r2["demand"]["override_reason"] == "Need extra buffer for Q3 interns"

    attention_ids = [item["id"] for item in r2["attention_items"]]
    assert "override_stale_cc-eng-001" in attention_ids

    stale_item = next(item for item in r2["attention_items"] if item["id"] == "override_stale_cc-eng-001")
    assert "Underlying inventory/asset data has changed" in stale_item["message"]
    assert "8" in stale_item["message"]
