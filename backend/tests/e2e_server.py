"""Run the real API with deterministic external dependencies for browser E2E tests."""

import os
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import uvicorn

os.environ["GEMINI_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from main import app  # noqa: E402

settings.GEMINI_API_KEY = ""


def categories(args):
    query = str(args["query"]).lower()
    if "monitor" in query:
        return [
            {
                "category_id": "IT-HW-02",
                "category_name": "IT Equipment > Monitors",
            }
        ]
    return [
        {
            "category_id": "GEN-SUPPLY",
            "category_name": "General Office & IT Supplies",
        }
    ]


def inventory(args):
    item_name = args["item_name"]
    return {
        "item": item_name,
        "available_quantity": 2 if str(item_name).lower() == "monitor" else 0,
    }


def assets(args):
    item_name = args["item_name"]
    return {
        "item": item_name,
        "total_available_soon": 3 if str(item_name).lower() == "monitor" else 0,
    }


def run():
    with ExitStack() as stack:
        node_categories = stack.enter_context(
            patch("app.agent.nodes.clarification_node.get_categories")
        )
        node_specifications = stack.enter_context(
            patch("app.agent.nodes.clarification_node.get_specifications")
        )
        node_policy = stack.enter_context(
            patch("app.agent.nodes.clarification_node.get_procurement_policy")
        )
        node_inventory = stack.enter_context(
            patch("app.agent.nodes.demand_node.get_inventory")
        )
        node_assets = stack.enter_context(
            patch("app.agent.nodes.demand_node.get_assets")
        )
        node_pipeline = stack.enter_context(
            patch("app.agent.nodes.demand_node.get_open_prs_and_pos")
        )
        node_history = stack.enter_context(
            patch("app.agent.nodes.demand_node.get_purchase_history")
        )
        node_budget = stack.enter_context(
            patch("app.agent.nodes.demand_node.get_budget_status")
        )

        node_categories.invoke.side_effect = categories
        node_specifications.invoke.return_value = {"standard_models": []}
        node_policy.invoke.return_value = {
            "policy_text": "Standard procurement policy.",
            "max_specs": {},
        }
        node_inventory.invoke.side_effect = inventory
        node_assets.invoke.side_effect = assets
        node_pipeline.invoke.return_value = {"total_in_pipeline": 0}
        node_history.invoke.return_value = {"average_unit_cost_usd": 350.0}
        node_budget.invoke.return_value = {
            "remaining_budget": 33_000.0,
            "currency": "USD",
        }

        uvicorn.run(app, host="127.0.0.1", port=8010)


if __name__ == "__main__":
    run()
