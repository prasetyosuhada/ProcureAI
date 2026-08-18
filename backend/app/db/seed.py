import asyncio
import logging
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.models.inventory import Inventory
from app.models.asset import Asset
from app.models.pipeline_order import PipelineOrder
from app.models.purchase_history import PurchaseHistory
from app.models.budget import Budget

logger = logging.getLogger(__name__)

INITIAL_INVENTORY = [
    {"item_name": "Laptop", "category_id": "IT-HW-01", "available_quantity": 3, "location": "IT Store Room A", "condition": "Unopened Box"},
    {"item_name": "Monitor", "category_id": "IT-HW-02", "available_quantity": 2, "location": "IT Store Room B", "condition": "Like New"},
    {"item_name": "Ergonomic Chair", "category_id": "OF-FURN-01", "available_quantity": 4, "location": "Warehouse Facilities C", "condition": "Good Condition"},
    {"item_name": "Standing Desk", "category_id": "OF-FURN-02", "available_quantity": 1, "location": "Warehouse Facilities C", "condition": "Good Condition"},
]

INITIAL_ASSETS = [
    {
        "item_name": "Laptop",
        "department_id": "DEPT-ENG",
        "currently_unused": 3,
        "scheduled_returns_next_30_days": 2,
        "total_available_soon": 5,
        "notes": "3 unused units in IT stock, 2 units scheduled for offboarding return by end of month."
    },
    {
        "item_name": "Monitor",
        "department_id": "DEPT-ENG",
        "currently_unused": 2,
        "scheduled_returns_next_30_days": 1,
        "total_available_soon": 3,
        "notes": "2 unused units in stock, 1 unit scheduled for return."
    },
    {
        "item_name": "Ergonomic Chair",
        "department_id": "DEPT-OPS",
        "currently_unused": 4,
        "scheduled_returns_next_30_days": 0,
        "total_available_soon": 4,
        "notes": "4 refurbished chairs available in facilities warehouse."
    }
]

INITIAL_PIPELINE = [
    {
        "item_name": "Laptop",
        "order_type": "PR",
        "reference_id": "PR-992",
        "requester": "Engineering",
        "vendor": None,
        "quantity": 2,
        "status": "PENDING_APPROVAL",
        "expected_delivery": None,
        "department_id": "DEPT-ENG"
    },
    {
        "item_name": "Laptop",
        "order_type": "PO",
        "reference_id": "PO-401",
        "requester": None,
        "vendor": "Dell Commercial",
        "quantity": 3,
        "status": "ORDERED",
        "expected_delivery": "2026-08-25",
        "department_id": "DEPT-ENG"
    }
]

INITIAL_PURCHASE_HISTORY = [
    {
        "item_name": "Laptop",
        "department_id": "DEPT-ENG",
        "last_12_months_total": 25,
        "average_order_quantity": 5,
        "last_order_date": "2026-03-15",
        "average_unit_cost_usd": 1500.00,
        "currency": "USD"
    },
    {
        "item_name": "Monitor",
        "department_id": "DEPT-ENG",
        "last_12_months_total": 12,
        "average_order_quantity": 4,
        "last_order_date": "2026-05-10",
        "average_unit_cost_usd": 350.00,
        "currency": "USD"
    },
    {
        "item_name": "Ergonomic Chair",
        "department_id": "DEPT-OPS",
        "last_12_months_total": 15,
        "average_order_quantity": 5,
        "last_order_date": "2026-04-12",
        "average_unit_cost_usd": 350.00,
        "currency": "USD"
    }
]

INITIAL_BUDGETS = [
    {
        "cost_center": "CC-ENG-001",
        "department_name": "Engineering",
        "department_id": "DEPT-ENG",
        "allocated_budget": 75000.00,
        "consumed_budget": 42000.00,
        "remaining_budget": 33000.00,
        "currency": "USD"
    },
    {
        "cost_center": "CC-FIN-002",
        "department_name": "Finance",
        "department_id": "DEPT-FIN",
        "allocated_budget": 30000.00,
        "consumed_budget": 12000.00,
        "remaining_budget": 18000.00,
        "currency": "USD"
    },
    {
        "cost_center": "CC-OPS-001",
        "department_name": "Operations",
        "department_id": "DEPT-OPS",
        "allocated_budget": 50000.00,
        "consumed_budget": 20000.00,
        "remaining_budget": 30000.00,
        "currency": "USD"
    }
]

async def seed_enterprise_data():
    """Seeds default enterprise data into PostgreSQL database."""
    print("🌱 Seeding Enterprise Data into PostgreSQL...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Clean existing records for idempotent seeding
            await session.execute(delete(Inventory))
            await session.execute(delete(Asset))
            await session.execute(delete(PipelineOrder))
            await session.execute(delete(PurchaseHistory))
            await session.execute(delete(Budget))

            # 2. Insert Inventory
            for inv in INITIAL_INVENTORY:
                session.add(Inventory(**inv))

            # 3. Insert Assets
            for ast in INITIAL_ASSETS:
                session.add(Asset(**ast))

            # 4. Insert Pipeline Orders
            for pipe in INITIAL_PIPELINE:
                session.add(PipelineOrder(**pipe))

            # 5. Insert Purchase History
            for hist in INITIAL_PURCHASE_HISTORY:
                session.add(PurchaseHistory(**hist))

            # 6. Insert Budgets
            for budg in INITIAL_BUDGETS:
                session.add(Budget(**budg))

        print("✅ Enterprise Data successfully seeded!")

if __name__ == "__main__":
    asyncio.run(seed_enterprise_data())
