import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.agent.nodes.demand_node import demand_analysis_node
from app.agent.state import GraphState, RequirementDraftSchema, DemandAnalysisSchema

@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify GET /health returns operational status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "ProcureAI" in data["app"]

@pytest.mark.asyncio
async def test_auth_me_endpoint_custom_and_default():
    """Verify GET /api/v1/auth/me returns parsed user context."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Default dev headers
        res1 = await client.get("/api/v1/auth/me")
        assert res1.status_code == 200
        data1 = res1.json()
        assert "user_id" in data1
        assert "department_id" in data1

        # Injected custom headers
        headers = {
            "X-User-ID": "usr_executive_888",
            "X-User-Name": "Jane Doe",
            "X-Department-ID": "DEPT-FIN",
            "X-Cost-Center": "CC-FIN-001"
        }
        res2 = await client.get("/api/v1/auth/me", headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["user_id"] == "usr_executive_888"
        assert data2["user_name"] == "Jane Doe"
        assert data2["department_id"] == "DEPT-FIN"
        assert data2["cost_center"] == "CC-FIN-001"

@pytest.mark.asyncio
async def test_chat_endpoint_with_requirement_override():
    """Verify POST /api/v1/chat processes manual requirement override directly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Update requirement directly",
            "requirement_override": {
                "item": "Ergonomic Chair",
                "category": "Office Furniture > Ergonomic Chairs",
                "quantity": 15,
                "purpose": "Operations Team Refit",
                "required_date": "2026-10-01",
                "specifications": {"lumbar_support": "adjustable", "mesh": "breathable"},
                "is_complete": True
            }
        }
        res = await client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["requirement_draft"]["item"] == "Ergonomic Chair"
        assert data["requirement_draft"]["quantity"] == 15
        assert data["requirement_draft"]["is_complete"] is True
        assert data["demand_analysis"] is not None
        assert data["demand_analysis"]["is_complete"] is True

@pytest.mark.asyncio
async def test_demand_math_edge_case_excess_stock():
    """Verify net demand is non-negative (0) when warehouse stock exceeds requested amount."""
    state: GraphState = {
        "messages": [],
        "user_context": {"user_id": "usr_01", "department_id": "DEPT-ENG", "cost_center": "CC-ENG-001"},
        "requirement_draft": RequirementDraftSchema(
            item="Laptop",
            category="Hardware / IT Equipment",
            quantity=2,  # Requested 2, but stock=3 + assets=5 (= 8 available)
            purpose="Temporary intern",
            required_date="2026-09-01",
            specifications={"ram": "16GB"},
            is_complete=True
        ).model_dump(),
        "demand_analysis": DemandAnalysisSchema(is_complete=False).model_dump(),
        "pr_draft": None,
        "next_agent": "Demand"
    }

    result = await demand_analysis_node(state)
    analysis = result["demand_analysis"]
    assert analysis["is_complete"] is True
    assert analysis["requested_quantity"] == 2
    assert analysis["available_inventory"] == 3
    assert analysis["available_assets"] == 5
    # Recommended buy must be 0 (internal stock covers 100%), never negative!
    assert analysis["recommended_quantity"] == 0
    assert result["next_agent"] == "GeneratePR"

@pytest.mark.asyncio
async def test_demand_math_edge_case_zero_stock():
    """Verify net demand equals full requested amount when warehouse stock and assets are 0."""
    state: GraphState = {
        "messages": [],
        "user_context": {"user_id": "usr_01", "department_id": "DEPT-UNKNOWN", "cost_center": "CC-ENG-001"},
        "requirement_draft": RequirementDraftSchema(
            item="Rare Industrial Machine",
            category="Manufacturing Equipment",
            quantity=4,
            purpose="Plant Expansion",
            required_date="2026-11-01",
            specifications={},
            is_complete=True
        ).model_dump(),
        "demand_analysis": DemandAnalysisSchema(is_complete=False).model_dump(),
        "pr_draft": None,
        "next_agent": "Demand"
    }

    result = await demand_analysis_node(state)
    analysis = result["demand_analysis"]
    assert analysis["is_complete"] is True
    assert analysis["requested_quantity"] == 4
    assert analysis["available_inventory"] == 0
    assert analysis["available_assets"] == 0
    assert analysis["recommended_quantity"] == 4
    assert result["next_agent"] == "GeneratePR"
