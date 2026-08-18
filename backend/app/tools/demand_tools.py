import asyncio
import concurrent.futures
import logging
from typing import Optional, Dict, Any, List
import asyncpg
from langchain_core.tools import tool
from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_pg_url() -> str:
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def _run_async_db(coro_fn, *args, **kwargs):
    """Executes an async database operation safely from both sync and async contexts."""
    async def _runner():
        return await coro_fn(*args, **kwargs)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(_runner())).result()
    else:
        return asyncio.run(_runner())

def _normalize_item_term(item_name: str) -> str:
    term = (item_name or "").strip().lower()
    if term.endswith("s") and not term.endswith("ss") and len(term) > 3:
        term = term[:-1]
    return term


async def _get_inventory_db(item_name: str, category_id: Optional[str] = None) -> Dict[str, Any]:
    item_clean = _normalize_item_term(item_name)
    pattern = f"%{item_clean}%"
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            # Query matching item name or category ID
            row = await conn.fetchrow(
                """
                SELECT item_name, available_quantity, location, condition 
                FROM inventory 
                WHERE LOWER(item_name) LIKE $1 
                   OR $2 LIKE '%' || LOWER(item_name) || '%'
                   OR ($3::TEXT IS NOT NULL AND (category_id = $3 OR LOWER($3) LIKE '%' || LOWER(item_name) || '%'))
                ORDER BY 
                    CASE 
                        WHEN LOWER(item_name) LIKE $1 THEN 1 
                        WHEN $2 LIKE '%' || LOWER(item_name) || '%' THEN 2 
                        ELSE 3 
                    END,
                    available_quantity DESC
                LIMIT 1
                """,
                pattern, item_clean, category_id
            )

            if row:
                return {
                    "item": row["item_name"],
                    "available_quantity": int(row["available_quantity"]),
                    "location": row["location"] or "Warehouse Facilities",
                    "condition": row["condition"] or "Standard"
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying inventory for '{item_name}': {e}")

    return {
        "item": item_name,
        "available_quantity": 0,
        "location": "N/A",
        "condition": "No stock available"
    }


@tool
def get_inventory(item_name: str, category_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve current warehouse or store room inventory for a specific item from PostgreSQL database.
    
    Args:
        item_name: Name of the item being queried (e.g. 'laptop', 'monitor', 'chair').
        category_id: Optional procurement category ID.
        
    Returns:
        Dictionary containing available stock quantity and warehouse location.
    """
    return _run_async_db(_get_inventory_db, item_name, category_id)


async def _get_assets_db(item_name: str) -> Dict[str, Any]:
    item_clean = _normalize_item_term(item_name)
    pattern = f"%{item_clean}%"
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            row = await conn.fetchrow(
                """
                SELECT item_name, currently_unused, scheduled_returns_next_30_days, total_available_soon, notes
                FROM assets
                WHERE LOWER(item_name) LIKE $1 OR $2 LIKE '%' || LOWER(item_name) || '%'
                ORDER BY 
                    CASE 
                        WHEN LOWER(item_name) LIKE $1 THEN 1 
                        WHEN $2 LIKE '%' || LOWER(item_name) || '%' THEN 2 
                        ELSE 3 
                    END,
                    total_available_soon DESC
                LIMIT 1
                """,
                pattern, item_clean
            )
            if row:
                return {
                    "item": row["item_name"],
                    "currently_unused": int(row["currently_unused"]),
                    "scheduled_returns_next_30_days": int(row["scheduled_returns_next_30_days"]),
                    "total_available_soon": int(row["total_available_soon"]),
                    "notes": row["notes"] or ""
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying assets for '{item_name}': {e}")

    return {
        "item": item_name,
        "currently_unused": 0,
        "scheduled_returns_next_30_days": 0,
        "total_available_soon": 0,
        "notes": "No available or returning assets found."
    }


@tool
def get_assets(item_name: str) -> Dict[str, Any]:
    """
    Retrieve existing organizational assets that are currently unused or scheduled to be returned soon from PostgreSQL database.
    
    Args:
        item_name: Name of the requested item (e.g. 'laptop', 'monitor', 'chair').
        
    Returns:
        Dictionary containing counts of unused assets and soon-to-be-returned assets.
    """
    return _run_async_db(_get_assets_db, item_name)


async def _get_open_prs_and_pos_db(item_name: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    item_clean = _normalize_item_term(item_name)
    pattern = f"%{item_clean}%"
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            if department_id:
                rows = await conn.fetch(
                    """
                    SELECT order_type, reference_id, requester, vendor, quantity, status, expected_delivery
                    FROM pipeline_orders
                    WHERE (LOWER(item_name) LIKE $1 OR $2 LIKE '%' || LOWER(item_name) || '%')
                      AND department_id = $3
                    """,
                    pattern, item_clean, department_id
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT order_type, reference_id, requester, vendor, quantity, status, expected_delivery
                    FROM pipeline_orders
                    WHERE LOWER(item_name) LIKE $1 OR $2 LIKE '%' || LOWER(item_name) || '%'
                    """,
                    pattern, item_clean
                )

            open_prs = []
            open_pos = []
            total_in_pipeline = 0

            for r in rows:
                qty = int(r["quantity"])
                total_in_pipeline += qty
                if str(r["order_type"]).upper() == "PR":
                    open_prs.append({
                        "pr_id": r["reference_id"],
                        "requester": r["requester"] or "Department",
                        "quantity": qty,
                        "status": r["status"]
                    })
                elif str(r["order_type"]).upper() == "PO":
                    open_pos.append({
                        "po_id": r["reference_id"],
                        "vendor": r["vendor"] or "Vendor",
                        "quantity": qty,
                        "expected_delivery": r["expected_delivery"] or "TBD"
                    })

            return {
                "open_prs": open_prs,
                "open_pos": open_pos,
                "total_in_pipeline": total_in_pipeline
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying pipeline for '{item_name}': {e}")

    return {
        "open_prs": [],
        "open_pos": [],
        "total_in_pipeline": 0
    }


@tool
def get_open_prs_and_pos(item_name: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve open Purchase Requisitions (PRs) and Purchase Orders (POs) currently in the procurement pipeline for an item from PostgreSQL database.
    
    Args:
        item_name: Name of the requested item (e.g. 'laptop', 'monitor').
        department_id: Optional department code to filter open requests.
        
    Returns:
        Dictionary listing open PRs, open POs, and total units in pipeline.
    """
    return _run_async_db(_get_open_prs_and_pos_db, item_name, department_id)


async def _get_purchase_history_db(item_name: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    item_clean = _normalize_item_term(item_name)
    pattern = f"%{item_clean}%"
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            row = await conn.fetchrow(
                """
                SELECT last_12_months_total, average_order_quantity, last_order_date, average_unit_cost_usd
                FROM purchase_history
                WHERE LOWER(item_name) LIKE $1 OR $2 LIKE '%' || LOWER(item_name) || '%'
                ORDER BY 
                    CASE 
                        WHEN LOWER(item_name) LIKE $1 THEN 1 
                        WHEN $2 LIKE '%' || LOWER(item_name) || '%' THEN 2 
                        ELSE 3 
                    END,
                    last_12_months_total DESC
                LIMIT 1
                """,
                pattern, item_clean
            )
            if row:
                return {
                    "last_12_months_total": int(row["last_12_months_total"]),
                    "average_order_quantity": int(row["average_order_quantity"]),
                    "last_order_date": row["last_order_date"] or "N/A",
                    "average_unit_cost_usd": float(row["average_unit_cost_usd"])
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying purchase history for '{item_name}': {e}")

    return {
        "last_12_months_total": 0,
        "average_order_quantity": 0,
        "last_order_date": "N/A",
        "average_unit_cost_usd": 0.00
    }


@tool
def get_purchase_history(item_name: str, department_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve historical purchasing data and average unit costs for an item from PostgreSQL database.
    
    Args:
        item_name: Name of the requested item (e.g. 'laptop', 'monitor').
        department_id: Optional department code.
        
    Returns:
        Dictionary containing historical order totals, average quantity, and unit cost.
    """
    return _run_async_db(_get_purchase_history_db, item_name, department_id)


async def _get_budget_status_db(cost_center: Optional[str] = "CC-ENG-001", category_id: Optional[str] = None) -> Dict[str, Any]:
    cc_key = (cost_center or "CC-ENG-001").strip().upper()
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            row = await conn.fetchrow(
                """
                SELECT cost_center, department_name, allocated_budget, consumed_budget, remaining_budget, currency
                FROM budgets
                WHERE UPPER(cost_center) = $1
                LIMIT 1
                """,
                cc_key
            )
            if row:
                return {
                    "cost_center": row["cost_center"],
                    "department_name": row["department_name"],
                    "allocated_budget": float(row["allocated_budget"]),
                    "consumed_budget": float(row["consumed_budget"]),
                    "remaining_budget": float(row["remaining_budget"]),
                    "currency": row["currency"] or "USD"
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying budget for '{cc_key}': {e}")

    # Graceful fallback for unregistered cost centers
    return {
        "cost_center": cc_key,
        "department_name": "General Department",
        "allocated_budget": 50000.00,
        "consumed_budget": 10000.00,
        "remaining_budget": 40000.00,
        "currency": "USD"
    }


@tool
def get_budget_status(cost_center: Optional[str] = "CC-ENG-001", category_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve allocated, consumed, and remaining budget for a specific cost center from PostgreSQL database.
    
    Args:
        cost_center: Cost center code (e.g. 'CC-ENG-001', 'CC-FIN-002'). Defaults to user's cost center.
        category_id: Optional procurement category ID.
        
    Returns:
        Dictionary containing allocated budget, consumed budget, remaining balance, and currency.
    """
    return _run_async_db(_get_budget_status_db, cost_center, category_id)
