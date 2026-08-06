import pytest
from app.agents.graph import build_procurement_graph
from app.agents.state import ProcurementStage, ProcurementState


def test_build_procurement_graph():
    graph = build_procurement_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_procurement_graph_execution():
    graph = build_procurement_graph()

    initial_state: ProcurementState = {
        "pr_id": "test-pr-123",
        "po_id": None,
        "gr_ids": [],
        "invoice_id": None,
        "current_stage": ProcurementStage.REQUISITION,
        "status": "SUBMITTED",
        "pr_data": {"total_amount": 1000.0},
        "po_data": None,
        "gr_data": [],
        "invoice_data": None,
        "validation_results": None,
        "sourcing_recommendations": None,
        "match_results": None,
        "requires_human_approval": False,
        "approval_type": None,
        "human_decision": None,
        "error": None,
        "history": []
    }

    result = await graph.ainvoke(initial_state)
    assert result["current_stage"] == ProcurementStage.APPROVED_FOR_PAYMENT
    assert result["status"] == "MATCH_CLEAN"
