import asyncio
import concurrent.futures
import json
import logging
from typing import Optional, List, Dict, Any
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

def _normalize_item_term(term: str) -> str:
    t = (term or "").strip().lower()
    if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
        t = t[:-1]
    return t


async def _get_categories_db(query: str) -> List[Dict[str, str]]:
    q_clean = _normalize_item_term(query)
    pattern = f"%{q_clean}%"
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            rows = await conn.fetch("SELECT category_id, category_name, keywords FROM procurement_categories")
            results = []
            for r in rows:
                cat_id = r["category_id"]
                cat_name = r["category_name"]
                kws = r["keywords"]
                if isinstance(kws, str):
                    try:
                        kws = json.loads(kws)
                    except Exception:
                        kws = []

                if (q_clean in cat_name.lower() or 
                    any(kw.lower() in q_clean or q_clean in kw.lower() for kw in kws) or 
                    q_clean in cat_id.lower()):
                    results.append({
                        "category_id": cat_id,
                        "category_name": cat_name
                    })

            if results:
                return results
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying procurement categories for '{query}': {e}")

    # Fallback category if query is not found
    return [{
        "category_id": "GEN-SUPPLY",
        "category_name": "General Office & IT Supplies"
    }]


@tool
def get_categories(query: str) -> List[Dict[str, str]]:
    """
    Look up standard enterprise procurement categories matching a search query from PostgreSQL database.
    
    Args:
        query: Natural language query of the requested item (e.g. 'laptop', 'monitor', 'ergonomic chair').
        
    Returns:
        List of matching procurement categories with category_id and category_name.
    """
    return _run_async_db(_get_categories_db, query)


async def _get_specifications_db(category_id: str, item_name: str) -> Dict[str, Any]:
    item_clean = _normalize_item_term(item_name)
    pattern = f"%{item_clean}%"
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            row = await conn.fetchrow(
                """
                SELECT standard_models 
                FROM standard_specifications 
                WHERE category_id = $1 
                   OR LOWER(item_name) LIKE $2 
                   OR $3 LIKE '%' || LOWER(item_name) || '%'
                ORDER BY 
                    CASE 
                        WHEN category_id = $1 THEN 1 
                        WHEN LOWER(item_name) LIKE $2 THEN 2 
                        ELSE 3 
                    END
                LIMIT 1
                """,
                category_id, pattern, item_clean
            )
            if row:
                models = row["standard_models"]
                if isinstance(models, str):
                    models = json.loads(models)
                return {"standard_models": models}
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying specifications for '{category_id}' / '{item_name}': {e}")

    # Generic fallback specification
    return {
        "standard_models": [
            {
                "model_name": f"Standard {item_name.title()}",
                "recommended_for": ["General Use"],
                "specs": {
                    "grade": "Commercial Standard",
                    "warranty": "3 Year On-Site"
                }
            }
        ]
    }


@tool
def get_specifications(category_id: str, item_name: str) -> Dict[str, Any]:
    """
    Retrieve company-approved standard models and specifications for a given category and item from PostgreSQL database.
    
    Args:
        category_id: Standard procurement category ID (e.g. 'IT-HW-01').
        item_name: Name of the requested item (e.g. 'Laptop').
        
    Returns:
        Dictionary containing company-standard models, target user roles, and hardware specs.
    """
    return _run_async_db(_get_specifications_db, category_id, item_name)


async def _get_procurement_policy_db(item_name: str, estimated_value: Optional[float] = None) -> Dict[str, Any]:
    item_clean = _normalize_item_term(item_name)
    try:
        conn = await asyncpg.connect(_get_pg_url())
        try:
            # Query all policies
            rows = await conn.fetch("SELECT policy_key, policy_text, approval_rules FROM procurement_policies")
            matched_policy_text = None
            matched_rules = {}

            # First match specific key
            for r in rows:
                pkey = str(r["policy_key"]).lower()
                if pkey in item_clean or item_clean in pkey:
                    matched_policy_text = r["policy_text"]
                    matched_rules = r["approval_rules"]
                    if isinstance(matched_rules, str):
                        matched_rules = json.loads(matched_rules)
                    break

            # Fallback to general policy
            if not matched_policy_text:
                for r in rows:
                    if str(r["policy_key"]).lower() == "general":
                        matched_policy_text = r["policy_text"]
                        matched_rules = r["approval_rules"]
                        if isinstance(matched_rules, str):
                            matched_rules = json.loads(matched_rules)
                        break

            if matched_policy_text:
                value_note = ""
                if estimated_value is not None:
                    if estimated_value > matched_rules.get("threshold_high", 5000):
                        value_note = " High-value purchase restriction: Requires Finance Director approval for orders over $5,000."
                    elif estimated_value > matched_rules.get("threshold_mid", 2000):
                        value_note = " Mid-value purchase restriction: Requires Department Head approval for orders over $2,000."

                return {
                    "item": item_name,
                    "policy_text": f"{matched_policy_text}{value_note}",
                    "requires_it_approval": matched_rules.get("requires_it_approval", "laptop" in item_clean or "monitor" in item_clean),
                    "requires_facilities_approval": matched_rules.get("requires_facilities_approval", "chair" in item_clean or "desk" in item_clean)
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Database error querying procurement policy for '{item_name}': {e}")

    # Fallback policy
    value_note = ""
    if estimated_value is not None:
        if estimated_value > 5000:
            value_note = " High-value purchase restriction: Requires Finance Director approval for orders over $5,000."
        elif estimated_value > 2000:
            value_note = " Mid-value purchase restriction: Requires Department Head approval for orders over $2,000."

    return {
        "item": item_name,
        "policy_text": f"All purchase requisitions must be justified with a business purpose and target completion date. Orders above $5,000 require competitive finance review.{value_note}",
        "requires_it_approval": "laptop" in item_clean or "monitor" in item_clean,
        "requires_facilities_approval": "chair" in item_clean or "desk" in item_clean
    }


@tool
def get_procurement_policy(item_name: str, estimated_value: Optional[float] = None) -> Dict[str, Any]:
    """
    Retrieve organizational procurement policies and approval rules relevant to an item or estimated purchase value from PostgreSQL database.
    
    Args:
        item_name: Name of the item being requested (e.g. 'laptop', 'chair').
        estimated_value: Optional total estimated purchase amount in USD.
        
    Returns:
        Dictionary containing human-readable policy text and threshold rules.
    """
    return _run_async_db(_get_procurement_policy_db, item_name, estimated_value)
