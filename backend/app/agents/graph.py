from langgraph.graph import END, START, StateGraph
from app.agents.state import ProcurementStage, ProcurementState


async def validate_requisition_node(state: ProcurementState) -> dict:
    """
    Placeholder node for Requisition Validation Agent.
    """
    return {
        "current_stage": ProcurementStage.PR_APPROVAL_PENDING,
        "status": "VALIDATED",
        "validation_results": {"is_valid": True, "anomalies_detected": []}
    }


async def sourcing_po_node(state: ProcurementState) -> dict:
    """
    Placeholder node for Sourcing & PO Agent.
    """
    return {
        "current_stage": ProcurementStage.GOODS_RECEIPT,
        "status": "PO_ISSUED"
    }


async def goods_receipt_node(state: ProcurementState) -> dict:
    """
    Placeholder node for Goods Receipt Agent.
    """
    return {
        "current_stage": ProcurementStage.INVOICE_MATCHING,
        "status": "GR_CONFIRMED"
    }


async def invoice_matching_node(state: ProcurementState) -> dict:
    """
    Placeholder node for Invoice 3-Way Matching Agent.
    """
    return {
        "current_stage": ProcurementStage.APPROVED_FOR_PAYMENT,
        "status": "MATCH_CLEAN"
    }


def build_procurement_graph():
    """
    Constructs and compiles the base LangGraph StateGraph for ProcureAI workflow.
    """
    builder = StateGraph(ProcurementState)

    # Add workflow nodes
    builder.add_node("validate_requisition", validate_requisition_node)
    builder.add_node("sourcing_po", sourcing_po_node)
    builder.add_node("goods_receipt", goods_receipt_node)
    builder.add_node("invoice_matching", invoice_matching_node)

    # Define edges between nodes
    builder.add_edge(START, "validate_requisition")
    builder.add_edge("validate_requisition", "sourcing_po")
    builder.add_edge("sourcing_po", "goods_receipt")
    builder.add_edge("goods_receipt", "invoice_matching")
    builder.add_edge("invoice_matching", END)

    return builder.compile()
