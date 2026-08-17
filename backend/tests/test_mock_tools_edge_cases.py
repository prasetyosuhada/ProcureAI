import pytest
from app.tools.clarification_tools import (
    get_categories,
    get_specifications,
    get_procurement_policy,
)
from app.tools.demand_tools import (
    get_inventory,
    get_assets,
    get_open_prs_and_pos,
    get_purchase_history,
    get_budget_status,
)

def test_clarification_tools_unknown_item_fallback():
    """Verify get_specifications handles unknown/unregistered items gracefully."""
    res = get_specifications.invoke({"category_id": "GEN-SUPPLY", "item_name": "quantum_computer_x99"})
    assert isinstance(res, dict)
    assert "standard_models" in res
    assert len(res["standard_models"]) >= 1
    assert "Commercial Standard" in res["standard_models"][0]["specs"]["grade"]

def test_clarification_categories_structure():
    """Verify get_categories returns structured catalog with matching search query."""
    res = get_categories.invoke({"query": "laptop"})
    assert isinstance(res, list)
    assert len(res) >= 1
    assert res[0]["category_id"] == "IT-HW-01"
    assert "Laptops" in res[0]["category_name"]

def test_clarification_categories_fallback_for_unknown():
    """Verify get_categories falls back to General Office & IT Supplies for unknown query."""
    res = get_categories.invoke({"query": "unknown_exotic_widget_12345"})
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["category_id"] == "GEN-SUPPLY"

def test_procurement_policy_limits_and_rules():
    """Verify get_procurement_policy returns approval thresholds for high vs standard spend."""
    res_high = get_procurement_policy.invoke({"item_name": "laptop", "estimated_value": 6000.0})
    assert res_high["item"] == "laptop"
    assert res_high["requires_it_approval"] is True
    assert "Finance Director approval" in res_high["policy_text"]

    res_standard = get_procurement_policy.invoke({"item_name": "chair", "estimated_value": 500.0})
    assert res_standard["requires_facilities_approval"] is True
    assert "warehouse assets" in res_standard["policy_text"]

def test_inventory_zero_stock_edge_case():
    """Verify get_inventory handles items with zero warehouse stock."""
    res = get_inventory.invoke({"item_name": "Projector 4K Ultra"})
    assert "available_quantity" in res
    assert res["available_quantity"] == 0
    assert res["condition"] == "No stock available"

def test_inventory_existing_stock():
    """Verify get_inventory returns accurate available stock for standard catalog items."""
    res = get_inventory.invoke({"item_name": "Laptop"})
    assert res["available_quantity"] == 3
    assert res["location"] == "IT Store Room A"
    assert res["condition"] == "Unopened Box"

def test_assets_returning_and_available():
    """Verify get_assets returns unallocated and scheduled returning assets."""
    res = get_assets.invoke({"item_name": "Laptop"})
    assert res["total_available_soon"] == 5
    assert res["currently_unused"] == 3
    assert res["scheduled_returns_next_30_days"] == 2

def test_assets_unknown_item():
    """Verify get_assets handles unknown item gracefully with zero counts."""
    res = get_assets.invoke({"item_name": "Antimatter Containment Unit"})
    assert res["total_available_soon"] == 0
    assert res["currently_unused"] == 0
    assert res["scheduled_returns_next_30_days"] == 0

def test_open_prs_and_pos_pipeline():
    """Verify get_open_prs_and_pos returns active requisitions in pipeline."""
    res = get_open_prs_and_pos.invoke({"item_name": "Laptop"})
    assert "open_prs" in res
    assert "open_pos" in res
    assert "total_in_pipeline" in res
    assert res["total_in_pipeline"] == 5

def test_purchase_history_vendor_and_pricing():
    """Verify get_purchase_history returns historical benchmark prices."""
    res = get_purchase_history.invoke({"item_name": "Laptop"})
    assert res["last_12_months_total"] == 25
    assert res["average_order_quantity"] == 5
    assert res["average_unit_cost_usd"] == 1500.0

def test_budget_status_healthy_and_custom_cost_centers():
    """Verify get_budget_status returns accurate budget limits, consumed, and remaining balance."""
    # Engineering cost center
    res_eng = get_budget_status.invoke({"cost_center": "CC-ENG-001"})
    assert res_eng["allocated_budget"] == 75000.0
    assert res_eng["consumed_budget"] == 42000.0
    assert res_eng["remaining_budget"] == 33000.0
    assert res_eng["currency"] == "USD"

    # Finance cost center
    res_fin = get_budget_status.invoke({"cost_center": "CC-FIN-002"})
    assert res_fin["allocated_budget"] == 30000.0
    assert res_fin["remaining_budget"] == 18000.0

    # Fallback cost center
    res_gen = get_budget_status.invoke({"cost_center": "CC-NEW-999"})
    assert res_gen["remaining_budget"] == 40000.0
