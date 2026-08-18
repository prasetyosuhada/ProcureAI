import asyncio
import logging
from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models.inventory import Inventory
from app.models.asset import Asset
from app.models.pipeline_order import PipelineOrder
from app.models.purchase_history import PurchaseHistory
from app.models.budget import Budget
from app.models.procurement_category import ProcurementCategory
from app.models.standard_specification import StandardSpecification
from app.models.procurement_policy import ProcurementPolicy

logger = logging.getLogger(__name__)

INITIAL_CATEGORIES = [
    {"category_id": "IT-HW-01", "category_name": "IT Equipment > Laptops", "keywords": ["laptop", "notebook", "macbook", "computer"]},
    {"category_id": "IT-HW-02", "category_name": "IT Equipment > Monitors", "keywords": ["monitor", "display", "screen"]},
    {"category_id": "IT-HW-03", "category_name": "IT Equipment > Peripherals", "keywords": ["keyboard", "mouse", "dock", "hub", "adapter"]},
    {"category_id": "OF-FURN-01", "category_name": "Office Furniture > Ergonomic Chairs", "keywords": ["chair", "seating", "desk chair"]},
    {"category_id": "OF-FURN-02", "category_name": "Office Furniture > Desks", "keywords": ["desk", "table", "standing desk"]},
    {"category_id": "SW-LIC-01", "category_name": "Software > Developer Tools", "keywords": ["ide", "software", "license", "jetbrains", "docker"]},
]

INITIAL_SPECS = [
    {
        "category_id": "IT-HW-01",
        "item_name": "Laptop",
        "standard_models": [
            {
                "model_name": "Standard Developer Laptop",
                "recommended_for": ["Backend Developer", "Frontend Developer", "Data Engineer", "DevOps"],
                "specs": {
                    "processor": "Intel i7 / Apple M-series Pro",
                    "ram": "32GB",
                    "storage": "1TB SSD",
                    "os": "macOS / Linux / Windows 11 Pro"
                }
            },
            {
                "model_name": "Standard Business Laptop",
                "recommended_for": ["General Staff", "Finance", "HR", "Sales", "Operations"],
                "specs": {
                    "processor": "Intel i5 / Apple M-series Base",
                    "ram": "16GB",
                    "storage": "512GB SSD",
                    "os": "Windows 11 Pro"
                }
            }
        ]
    },
    {
        "category_id": "IT-HW-02",
        "item_name": "Monitor",
        "standard_models": [
            {
                "model_name": "Standard 27-inch 4K Monitor",
                "recommended_for": ["Designer", "Developer", "General"],
                "specs": {
                    "resolution": "3840x2160 (4K)",
                    "size": "27 inch",
                    "connectivity": "USB-C with Power Delivery, HDMI, DisplayPort"
                }
            }
        ]
    },
    {
        "category_id": "OF-FURN-01",
        "item_name": "Ergonomic Chair",
        "standard_models": [
            {
                "model_name": "Ergonomic Mesh Task Chair",
                "recommended_for": ["All Employees"],
                "specs": {
                    "lumbar_support": "Adjustable",
                    "armrests": "3D Adjustable",
                    "weight_capacity": "136 kg"
                }
            }
        ]
    },
    {
        "category_id": "OF-FURN-02",
        "item_name": "Standing Desk",
        "standard_models": [
            {
                "model_name": "Electric Dual-Motor Standing Desk",
                "recommended_for": ["All Employees"],
                "specs": {
                    "height_range": "62cm - 128cm",
                    "dimensions": "140cm x 70cm",
                    "weight_capacity": "100 kg"
                }
            }
        ]
    }
]

INITIAL_POLICIES = [
    {
        "policy_key": "laptop",
        "item_category": "IT Hardware",
        "policy_text": "All IT hardware requests require IT Department validation. Standard developer laptops are configured with 32GB RAM for local Docker execution. Purchase value above $2,000 requires VP/Department Head approval.",
        "approval_rules": {"requires_it_approval": True, "requires_facilities_approval": False, "threshold_mid": 2000, "threshold_high": 5000}
    },
    {
        "policy_key": "monitor",
        "item_category": "IT Hardware",
        "policy_text": "Maximum 2 external monitors allowed per employee. Standard specification is 27-inch 4K USB-C.",
        "approval_rules": {"requires_it_approval": True, "requires_facilities_approval": False, "threshold_mid": 2000, "threshold_high": 5000}
    },
    {
        "policy_key": "chair",
        "item_category": "Office Furniture",
        "policy_text": "Ergonomic furniture requests must be fulfilled from existing warehouse assets if available. Purchases require Facilities approval.",
        "approval_rules": {"requires_it_approval": False, "requires_facilities_approval": True, "threshold_mid": 2000, "threshold_high": 5000}
    },
    {
        "policy_key": "desk",
        "item_category": "Office Furniture",
        "policy_text": "Standing desks require Facilities review and ergonomic workstation justification. Standard size is 140x70cm dual-motor.",
        "approval_rules": {"requires_it_approval": False, "requires_facilities_approval": True, "threshold_mid": 2000, "threshold_high": 5000}
    },
    {
        "policy_key": "general",
        "item_category": "General",
        "policy_text": "All purchase requisitions must be justified with a business purpose and target completion date. Orders above $5,000 require competitive finance review.",
        "approval_rules": {"requires_it_approval": False, "requires_facilities_approval": False, "threshold_mid": 2000, "threshold_high": 5000}
    }
]

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
    """Seeds comprehensive enterprise data into PostgreSQL database."""
    print("🌱 Seeding Enterprise Data into PostgreSQL...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Clean existing records for idempotent seeding
            await session.execute(delete(ProcurementCategory))
            await session.execute(delete(StandardSpecification))
            await session.execute(delete(ProcurementPolicy))
            await session.execute(delete(Inventory))
            await session.execute(delete(Asset))
            await session.execute(delete(PipelineOrder))
            await session.execute(delete(PurchaseHistory))
            await session.execute(delete(Budget))

            # 2. Insert Categories
            for cat in INITIAL_CATEGORIES:
                session.add(ProcurementCategory(**cat))

            # 3. Insert Specs
            for spec in INITIAL_SPECS:
                session.add(StandardSpecification(**spec))

            # 4. Insert Policies
            for pol in INITIAL_POLICIES:
                session.add(ProcurementPolicy(**pol))

            # 5. Insert Inventory
            for inv in INITIAL_INVENTORY:
                session.add(Inventory(**inv))

            # 6. Insert Assets
            for ast in INITIAL_ASSETS:
                session.add(Asset(**ast))

            # 7. Insert Pipeline Orders
            for pipe in INITIAL_PIPELINE:
                session.add(PipelineOrder(**pipe))

            # 8. Insert Purchase History
            for hist in INITIAL_PURCHASE_HISTORY:
                session.add(PurchaseHistory(**hist))

            # 9. Insert Budgets
            for budg in INITIAL_BUDGETS:
                session.add(Budget(**budg))

        print("✅ Enterprise Data successfully seeded!")

if __name__ == "__main__":
    asyncio.run(seed_enterprise_data())
