from typing import Optional, Dict, Any
from langchain_core.tools import tool

# Mock Data Store for Warehouse Inventory
MOCK_INVENTORY = {
    "laptop": {"item": "Laptop", "available_quantity": 3, "location": "IT Store Room A", "condition": "Unopened Box"},
    "monitor": {"item": "Monitor", "available_quantity": 2, "location": "IT Store Room B", "condition": "Like New"},
    "chair": {"item": "Ergonomic Chair", "available_quantity": 4, "location": "Warehouse Facilities C", "condition": "Good Condition"},
    "desk": {"item": "Standing Desk", "available_quantity": 1, "location": "Warehouse Facilities C", "condition": "Good Condition"}
}

# Mock Data Store for Organizational Assets
MOCK_ASSETS = {
    "laptop": {
        "item": "Laptop",
        "currently_unused": 3,
        "scheduled_returns_next_30_days": 2,
        "total_available_soon": 5,
        "notes": "3 unused units in IT stock, 2 units scheduled for offboarding return by end of month."
    },
    "monitor": {
        "item": "Monitor",
        "currently_unused": 2,
        "scheduled_returns_next_30_days": 1,
        "total_available_soon": 3,
        "notes": "2 unused units in stock, 1 unit scheduled for return."
    },
    "chair": {
        "item": "Ergonomic Chair",
        "currently_unused": 4,
        "scheduled_returns_next_30_days": 0,
        "total_available_soon": 4,
        "notes": "4 refurbished chairs available in facilities warehouse."
    }
}

# Mock Data Store for Open Purchase Requisitions & Orders
MOCK_PIPELINE = {
    "laptop": {
        "open_prs": [
            {"pr_id": "PR-992", "requester": "Engineering", "quantity": 2, "status": "PENDING_APPROVAL"}
        ],
        "open_pos": [
            {"po_id": "PO-401", "vendor": "Dell Commercial", "quantity": 3, "expected_delivery": "2026-08-25"}
        ],
        "total_in_pipeline": 5
    },
    "monitor": {
        "open_prs": [],
        "open_pos": [],
        "total_in_pipeline": 0
    }
}

# Mock Data Store for Purchase History
MOCK_HISTORY = {
    "laptop": {
        "last_12_months_total": 25,
        "average_order_quantity": 5,
        "last_order_date": "2026-03-15",
        "average_unit_cost_usd": 1500.00
    },
    "monitor": {
        "last_12_months_total": 12,
        "average_order_quantity": 4,
        "last_order_date": "2026-05-10",
        "average_unit_cost_usd": 350.00
    }
}

# Mock Data Store for Department Budgets
MOCK_BUDGETS = {
    "CC-ENG-001": {
        "cost_center": "CC-ENG-001",
        "department_name": "Engineering",
        "allocated_budget": 75000.00,
        "consumed_budget": 42000.00,
        "remaining_budget": 33000.00,
        "currency": "USD"
    },
    "CC-FIN-002": {
        "cost_center": "CC-FIN-002",
        "department_name": "Finance",
        "allocated_budget": 30000.00,
        "consumed_budget": 12000.00,
        "remaining_budget": 18000.00,
        "currency": "USD"
    }
}


@tool
def get_inventory(item_name: str, category_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve current warehouse or store room inventory for a specific item.
    
    Args:
        item_name: Name of the item being queried (e.g. 'laptop', 'monitor', 'chair').
        category_id: Optional procurement category ID.
        
    Returns:
        Dictionary containing available stock quantity and warehouse location.
    """
    item_lower = item_name.lower().strip()
    
    for key, data in MOCK_INVENTORY.items():
        if key in item_lower:
            return data
            
    return {
        "item": item_name,
        "available_quantity": 0,
        "location": "N/A",
        "condition": "No stock available"
    }


@tool
def get_assets(item_name: str) -> Dict[str, Any]:
    """
    Retrieve existing organizational assets that are currently unused or scheduled to be returned soon.
    
    Args:
        item_name: Name of the requested item (e.g. 'laptop', 'monitor', 'chair').
        
    Returns:
        Dictionary containing counts of unused assets and soon-to-be-returned assets.
    """
    item_lower = item_name.lower().strip()
    
    for key, data in MOCK_ASSETS.items():
        if key in item_lower:
            return data
            
    return {
        "item": item_name,
        "currently_unused": 0,
        "scheduled_returns_next_30_days": 0,
        "total_available_soon": 0,
        "notes": "No available or returning assets found."
    }


@tool
def get_open_prs_and_pos(item_name: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve open Purchase Requisitions (PRs) and Purchase Orders (POs) currently in the procurement pipeline for an item.
    
    Args:
        item_name: Name of the requested item (e.g. 'laptop', 'monitor').
        department_id: Optional department code to filter open requests.
        
    Returns:
        Dictionary listing open PRs, open POs, and total units in pipeline.
    """
    item_lower = item_name.lower().strip()
    
    for key, data in MOCK_PIPELINE.items():
        if key in item_lower:
            return data
            
    return {
        "open_prs": [],
        "open_pos": [],
        "total_in_pipeline": 0
    }


@tool
def get_purchase_history(item_name: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve historical purchasing data and average unit costs for an item over the past 12 months.
    
    Args:
        item_name: Name of the requested item (e.g. 'laptop', 'monitor').
        department_id: Optional department code.
        
    Returns:
        Dictionary containing historical order totals, average quantity, and unit cost.
    """
    item_lower = item_name.lower().strip()
    
    for key, data in MOCK_HISTORY.items():
        if key in item_lower:
            return data
            
    return {
        "last_12_months_total": 0,
        "average_order_quantity": 0,
        "last_order_date": "N/A",
        "average_unit_cost_usd": 0.00
    }


@tool
def get_budget_status(cost_center: Optional[str] = "CC-ENG-001", category_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve allocated, consumed, and remaining budget for a specific cost center.
    
    Args:
        cost_center: Cost center code (e.g. 'CC-ENG-001', 'CC-FIN-002'). Defaults to user's cost center.
        category_id: Optional procurement category ID.
        
    Returns:
        Dictionary containing allocated budget, consumed budget, remaining balance, and currency.
    """
    cc_key = cost_center.upper() if cost_center else "CC-ENG-001"
    
    budget_data = MOCK_BUDGETS.get(cc_key)
    if budget_data:
        return budget_data
        
    return {
        "cost_center": cc_key,
        "department_name": "General Department",
        "allocated_budget": 50000.00,
        "consumed_budget": 10000.00,
        "remaining_budget": 40000.00,
        "currency": "USD"
    }
