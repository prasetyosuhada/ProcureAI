import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.user import User
from app.models.budget import Budget
from app.models.vendor import Vendor, VendorPrice
from app.core.security import get_password_hash

async def seed_users(session: AsyncSession):
    # Check if users already exist
    result = await session.execute(select(User).limit(1))
    if result.scalars().first():
        print("Users already seeded.")
        return

    users_data = [
        {"email": "requester@procure.ai", "full_name": "Alice Requester", "role": "REQUESTER", "department": "IT"},
        {"email": "officer@procure.ai", "full_name": "Bob Officer", "role": "PROCUREMENT_OFFICER", "department": "Procurement"},
        {"email": "warehouse@procure.ai", "full_name": "Charlie Warehouse", "role": "WAREHOUSE_STAFF", "department": "Operations"},
        {"email": "ap@procure.ai", "full_name": "Diana AP", "role": "AP_CLERK", "department": "Finance"},
        {"email": "manager@procure.ai", "full_name": "Eve Manager", "role": "FINANCE_MANAGER", "department": "Finance"},
    ]

    hashed_password = get_password_hash("password123")
    for data in users_data:
        user = User(
            email=data["email"],
            full_name=data["full_name"],
            role=data["role"],
            department=data["department"],
            hashed_password=hashed_password
        )
        session.add(user)
    
    print("Users seeded.")

async def seed_budgets(session: AsyncSession):
    result = await session.execute(select(Budget).limit(1))
    if result.scalars().first():
        print("Budgets already seeded.")
        return

    budgets_data = [
        {"budget_code": "BG-IT-2026", "department": "IT", "fiscal_year": 2026, "allocated_amount": Decimal("100000.00")},
        {"budget_code": "BG-OPS-2026", "department": "Operations", "fiscal_year": 2026, "allocated_amount": Decimal("50000.00")},
        {"budget_code": "BG-MKT-2026", "department": "Marketing", "fiscal_year": 2026, "allocated_amount": Decimal("75000.00")},
    ]

    for data in budgets_data:
        budget = Budget(**data)
        session.add(budget)
    
    print("Budgets seeded.")

async def seed_vendors(session: AsyncSession):
    result = await session.execute(select(Vendor).limit(1))
    if result.scalars().first():
        print("Vendors already seeded.")
        return

    vendors = [
        Vendor(vendor_code="VEND-001", name="TechSupply Inc", contact_email="sales@techsupply.com", payment_terms="NET30"),
        Vendor(vendor_code="VEND-002", name="OfficeMart", contact_email="b2b@officemart.com", payment_terms="NET15"),
        Vendor(vendor_code="VEND-003", name="Global Hardware", contact_email="orders@globalhw.com", payment_terms="NET60"),
    ]
    
    session.add_all(vendors)
    await session.flush() # Flush to populate IDs

    prices = [
        VendorPrice(vendor_id=vendors[0].id, item_category="Hardware", item_name="NVIDIA RTX 4090 GPU 24GB", unit_price=Decimal("1500.00")),
        VendorPrice(vendor_id=vendors[0].id, item_category="Hardware", item_name="DDR5 RAM 64GB Kit", unit_price=Decimal("200.00")),
        VendorPrice(vendor_id=vendors[1].id, item_category="Office Equipment", item_name="Ergonomic Chair", unit_price=Decimal("350.00")),
        VendorPrice(vendor_id=vendors[2].id, item_category="Hardware", item_name="Server Rack 42U", unit_price=Decimal("800.00")),
    ]
    
    session.add_all(prices)
    print("Vendors and VendorPrices seeded.")

async def main():
    async with async_session_maker() as session:
        async with session.begin():
            await seed_users(session)
            await seed_budgets(session)
            await seed_vendors(session)
        print("Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
