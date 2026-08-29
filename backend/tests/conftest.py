import os
from unittest.mock import patch
import pytest

# Ensure offline mock mode for fast unit tests
os.environ["GEMINI_API_KEY"] = ""
from app.core.config import settings
settings.GEMINI_API_KEY = ""


@pytest.fixture(autouse=True)
def mock_agent_external_dependencies():
    """Make all DB-backed tools deterministic while preserving their public contracts."""
    async def mock_categories(query):
        query = str(query).lower()
        if "laptop" in query:
            return [{"category_id": "IT-HW-01", "category_name": "IT Equipment > Laptops"}]
        if "monitor" in query:
            return [{"category_id": "IT-HW-02", "category_name": "IT Equipment > Monitors"}]
        if "chair" in query:
            return [{"category_id": "OF-FURN-01", "category_name": "Office Furniture > Ergonomic Chairs"}]
        if "desk" in query:
            return [{"category_id": "OF-FURN-02", "category_name": "Office Furniture > Desks"}]
        return [{"category_id": "GEN-SUPPLY", "category_name": "General Office & IT Supplies"}]

    async def mock_specs(category_id, item_name):
        if category_id == "IT-HW-01" or str(item_name).lower() == "laptop":
            return {
                "standard_models": [
                    {
                        "model_name": "Standard Developer Laptop",
                        "recommended_for": ["Backend Developer"],
                        "specs": {"ram": "32GB", "storage": "1TB SSD"},
                    },
                    {
                        "model_name": "Standard Business Laptop",
                        "recommended_for": ["General Staff"],
                        "specs": {"ram": "16GB", "storage": "512GB SSD"},
                    },
                ]
            }
        return {"standard_models": [{"model_name": f"Standard {item_name.title()}", "specs": {"grade": "Commercial Standard"}}]}

    async def mock_policy(item_name, estimated_value=None):
        item = str(item_name).lower()
        value_note = ""
        if estimated_value is not None and estimated_value > 5000:
            value_note = " High-value purchase restriction: Requires Finance Director approval."
        if "chair" in item:
            text = "Ergonomic furniture requests must be fulfilled from existing warehouse assets if available."
        else:
            text = "Standard procurement policy."
        return {
            "item": item_name,
            "policy_text": f"{text}{value_note}",
            "requires_it_approval": "laptop" in item or "monitor" in item,
            "requires_facilities_approval": "chair" in item or "desk" in item,
        }

    async def mock_inventory(item_name, category_id=None):
        values = {
            "laptop": ("Laptop", 3, "IT Store Room A", "Unopened Box"),
            "monitor": ("Monitor", 2, "IT Store Room B", "Like New"),
            "ergonomic chair": ("Ergonomic Chair", 4, "Warehouse Facilities C", "Good Condition"),
            "standing desk": ("Standing Desk", 1, "Warehouse Facilities C", "Good Condition"),
        }
        item, quantity, location, condition = values.get(str(item_name).lower(), (item_name, 0, "N/A", "No stock available"))
        return {"item": item, "available_quantity": quantity, "location": location, "condition": condition}

    async def mock_assets(item_name):
        values = {
            "laptop": ("Laptop", 3, 2, 5),
            "monitor": ("Monitor", 2, 1, 3),
            "ergonomic chair": ("Ergonomic Chair", 4, 0, 4),
        }
        item, unused, returns, total = values.get(str(item_name).lower(), (item_name, 0, 0, 0))
        return {"item": item, "currently_unused": unused, "scheduled_returns_next_30_days": returns, "total_available_soon": total, "notes": "Test asset data"}

    async def mock_pipeline(item_name, department_id=None):
        if str(item_name).lower() == "laptop":
            return {"open_prs": [{"pr_id": "PR-992", "quantity": 2}], "open_pos": [{"po_id": "PO-401", "quantity": 3}], "total_in_pipeline": 5}
        return {"open_prs": [], "open_pos": [], "total_in_pipeline": 0}

    async def mock_history(item_name, department_id=None):
        values = {"laptop": (25, 5, 1500.0), "monitor": (12, 4, 350.0), "ergonomic chair": (15, 5, 350.0)}
        total, average_qty, unit_cost = values.get(str(item_name).lower(), (0, 0, 0.0))
        return {"last_12_months_total": total, "average_order_quantity": average_qty, "last_order_date": "2026-01-01", "average_unit_cost_usd": unit_cost}

    async def mock_budget(cost_center=None, category_id=None):
        cc = cost_center or "CC-ENG-001"
        if cc == "CC-ENG-001":
            return {"cost_center": cc, "allocated_budget": 75000.0, "consumed_budget": 42000.0, "remaining_budget": 33000.0, "currency": "USD"}
        if cc == "CC-FIN-002":
            return {"cost_center": cc, "allocated_budget": 30000.0, "consumed_budget": 12000.0, "remaining_budget": 18000.0, "currency": "USD"}
        return {"cost_center": cc, "allocated_budget": 50000.0, "consumed_budget": 10000.0, "remaining_budget": 40000.0, "currency": "USD"}

    with patch("app.tools.clarification_tools._get_categories_db", side_effect=mock_categories), \
         patch("app.tools.clarification_tools._get_specifications_db", side_effect=mock_specs), \
         patch("app.tools.clarification_tools._get_procurement_policy_db", side_effect=mock_policy), \
         patch("app.tools.demand_tools._get_inventory_db", side_effect=mock_inventory), \
         patch("app.tools.demand_tools._get_assets_db", side_effect=mock_assets), \
         patch("app.tools.demand_tools._get_open_prs_and_pos_db", side_effect=mock_pipeline), \
         patch("app.tools.demand_tools._get_purchase_history_db", side_effect=mock_history), \
         patch("app.tools.demand_tools._get_budget_status_db", side_effect=mock_budget), \
         patch("app.agent.nodes.clarification_node.get_categories") as node_categories, \
         patch("app.agent.nodes.clarification_node.get_specifications") as node_specifications, \
         patch("app.agent.nodes.clarification_node.get_procurement_policy") as node_policy, \
         patch("app.agent.nodes.demand_node.get_inventory") as node_inventory, \
         patch("app.agent.nodes.demand_node.get_assets") as node_assets, \
         patch("app.agent.nodes.demand_node.get_open_prs_and_pos") as node_pipeline, \
         patch("app.agent.nodes.demand_node.get_purchase_history") as node_history, \
         patch("app.agent.nodes.demand_node.get_budget_status") as node_budget:
        node_categories.invoke.side_effect = lambda args: (
            [{"category_id": "IT-HW-01", "category_name": "IT Equipment > Laptops"}] if "laptop" in args["query"].lower() else
            [{"category_id": "IT-HW-02", "category_name": "IT Equipment > Monitors"}] if "monitor" in args["query"].lower() else
            [{"category_id": "OF-FURN-01", "category_name": "Office Furniture > Ergonomic Chairs"}] if "chair" in args["query"].lower() else
            [{"category_id": "OF-FURN-02", "category_name": "Office Furniture > Desks"}] if "desk" in args["query"].lower() else
            [{"category_id": "GEN-SUPPLY", "category_name": "General Office & IT Supplies"}]
        )
        node_specifications.invoke.return_value = {"standard_models": []}
        node_policy.invoke.return_value = {"policy_text": "Standard policy", "max_specs": {"ram": "32GB"}}
        node_inventory.invoke.side_effect = lambda args: {
            "item": args["item_name"],
            "available_quantity": {"Laptop": 3, "Monitor": 2, "Ergonomic Chair": 4, "Standing Desk": 1}.get(args["item_name"], 0),
        }
        node_assets.invoke.side_effect = lambda args: {
            "item": args["item_name"],
            "total_available_soon": {"Laptop": 5, "Monitor": 3, "Ergonomic Chair": 4}.get(args["item_name"], 0),
        }
        node_pipeline.invoke.return_value = {"total_in_pipeline": 0}
        node_history.invoke.return_value = {"average_unit_cost": 1_500}
        node_budget.invoke.return_value = {"remaining_budget": 33_000, "currency": "USD"}
        yield
