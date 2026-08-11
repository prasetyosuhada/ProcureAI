import pytest
from app.tools.demand_tools import (
    get_inventory,
    get_assets,
    get_open_prs_and_pos,
    get_purchase_history,
    get_budget_status,
)

def test_get_inventory_laptop():
    """Test get_inventory tool for laptops."""
    res = get_inventory.invoke({"item_name": "laptop"})
    assert res["item"] == "Laptop"
    assert res["available_quantity"] == 3
    assert "Store Room" in res["location"]

def test_get_inventory_fallback():
    """Test get_inventory tool for unstocked item."""
    res = get_inventory.invoke({"item_name": "ergonomic keyboard xyz"})
    assert res["available_quantity"] == 0

def test_get_assets_laptop():
    """Test get_assets tool for existing/returning laptops."""
    res = get_assets.invoke({"item_name": "laptop"})
    assert res["currently_unused"] == 3
    assert res["scheduled_returns_next_30_days"] == 2
    assert res["total_available_soon"] == 5

def test_get_open_prs_and_pos():
    """Test get_open_prs_and_pos pipeline for laptops."""
    res = get_open_prs_and_pos.invoke({"item_name": "laptop"})
    assert len(res["open_prs"]) == 1
    assert len(res["open_pos"]) == 1
    assert res["total_in_pipeline"] == 5

def test_get_purchase_history():
    """Test get_purchase_history for laptops."""
    res = get_purchase_history.invoke({"item_name": "laptop"})
    assert res["last_12_months_total"] == 25
    assert res["average_unit_cost_usd"] == 1500.00

def test_get_budget_status_eng():
    """Test get_budget_status for engineering cost center."""
    res = get_budget_status.invoke({"cost_center": "CC-ENG-001"})
    assert res["cost_center"] == "CC-ENG-001"
    assert res["remaining_budget"] == 33000.00

def test_demand_tools_langchain_metadata():
    """Verify tool metadata for all 5 demand analysis tools."""
    assert get_inventory.name == "get_inventory"
    assert get_assets.name == "get_assets"
    assert get_open_prs_and_pos.name == "get_open_prs_and_pos"
    assert get_purchase_history.name == "get_purchase_history"
    assert get_budget_status.name == "get_budget_status"
