import pytest_asyncio
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db_session
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User
from app.models.budget import Budget

# SQLite in-memory database for fast, self-contained testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed initial test data in memory
    async with TestingSessionLocal() as session:
        hashed_password = get_password_hash("password123")
        users = [
            User(
                email="requester@procure.ai",
                full_name="Alice Requester",
                role="REQUESTER",
                department="IT",
                hashed_password=hashed_password,
            ),
            User(
                email="officer@procure.ai",
                full_name="Bob Officer",
                role="PROCUREMENT_OFFICER",
                department="Procurement",
                hashed_password=hashed_password,
            ),
            User(
                email="manager@procure.ai",
                full_name="Eve Manager",
                role="FINANCE_MANAGER",
                department="Finance",
                hashed_password=hashed_password,
            ),
        ]
        session.add_all(users)

        budget = Budget(
            budget_code="BG-IT-2026",
            department="IT",
            fiscal_year=2026,
            allocated_amount=Decimal("100000.00"),
            spent_amount=Decimal("0.00"),
            reserved_amount=Decimal("0.00"),
        )
        session.add(budget)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture()
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture()
async def async_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
