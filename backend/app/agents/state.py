from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class ProcurementStage(str, Enum):
    REQUISITION = "requisition"
    PR_APPROVAL_PENDING = "pr_approval_pending"
    SOURCING_PO = "sourcing_po"
    GOODS_RECEIPT = "goods_receipt"
    INVOICE_MATCHING = "invoice_matching"
    DISCREPANCY_REVIEW = "discrepancy_review"
    APPROVED_FOR_PAYMENT = "approved_for_payment"
    REJECTED = "rejected"


class ProcurementState(TypedDict):
    # Lifecycle Identifiers
    pr_id: str
    po_id: Optional[str]
    gr_ids: List[str]
    invoice_id: Optional[str]

    # Current Pipeline Stage & Status
    current_stage: ProcurementStage
    status: str

    # Stage Data Payload
    pr_data: Dict[str, Any]
    po_data: Optional[Dict[str, Any]]
    gr_data: List[Dict[str, Any]]
    invoice_data: Optional[Dict[str, Any]]

    # Agent Reasoning & Evaluation Artifacts
    validation_results: Optional[Dict[str, Any]]
    sourcing_recommendations: Optional[List[Dict[str, Any]]]
    match_results: Optional[Dict[str, Any]]

    # Governance & HITL Flags
    requires_human_approval: bool
    approval_type: Optional[str]  # "PR_APPROVAL" | "DISCREPANCY_RESOLUTION"
    human_decision: Optional[Dict[str, Any]]

    # Graph Control Metadata
    error: Optional[str]
    history: List[Dict[str, Any]]
