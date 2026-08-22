import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from app.agent.state import (
    ProcureAIState,
    GraphState,
    RequestProgress,
    PRSpecification,
    PRArtifact,
    DemandBreakdown,
    AgentAction,
    AttentionItem,
    update_specification,
    reduce_attention_items,
    reduce_agent_activity,
    reduce_pr_artifact,
    reduce_progress,
    reduce_demand,
    create_initial_graph_state,
    RequirementDraftSchema,
    DemandAnalysisSchema,
    PRDraftSchema,
)

def test_pr_specification_and_update_logic():
    """Verify PRSpecification models and reset rule in update_specification()."""
    spec = PRSpecification(field_name="RAM", value="16GB", is_confirmed=True)
    assert spec.is_confirmed is True

    # 1. Value changed -> is_confirmed must reset to False
    updated = update_specification(spec, new_value="32GB")
    assert updated.value == "32GB"
    assert updated.is_confirmed is False

    # 2. Value unchanged -> is_confirmed stays True
    unchanged = update_specification(spec, new_value="16GB")
    assert unchanged.value == "16GB"
    assert unchanged.is_confirmed is True

    # 3. Explicit confirmation passed
    explicit = update_specification(spec, new_value="64GB", new_is_confirmed=True)
    assert explicit.value == "64GB"
    assert explicit.is_confirmed is True


def test_demand_breakdown_schema():
    """Verify DemandBreakdown schema including manual override fields."""
    breakdown = DemandBreakdown(
        requested_qty=10,
        existing_inventory=3,
        assignable_assets=2,
        reserved_qty=1,
        net_new_purchase=6,
        estimated_saving=12000.0,
        is_manually_overridden=True,
        override_reason="Need extra buffer for Q3 interns"
    )
    data = breakdown.model_dump()
    assert data["requested_qty"] == 10
    assert data["net_new_purchase"] == 6
    assert data["is_manually_overridden"] is True
    assert data["override_reason"] == "Need extra buffer for Q3 interns"


def test_attention_items_reducer_dedup_and_anti_overwrite():
    """Verify reduce_attention_items upserts by deterministic ID and protects resolved=True."""
    existing = [
        {"id": "spec_ram", "category": "specification", "severity": "warning", "message": "RAM not standard", "resolved": True},
        {"id": "budget_cc-eng-001", "category": "budget", "severity": "blocking", "message": "Over budget", "resolved": False}
    ]
    incoming = [
        # re-emission of resolved item -> must NOT overwrite resolved=True
        {"id": "spec_ram", "category": "specification", "severity": "warning", "message": "RAM not standard (re-checked)", "resolved": False},
        # re-emission of unresolved item -> updates message
        {"id": "budget_cc-eng-001", "category": "budget", "severity": "blocking", "message": "Over budget by $5,000", "resolved": False},
        # new item -> inserted
        {"id": "policy_vp_threshold", "category": "policy", "severity": "warning", "message": "Requires VP sign-off", "resolved": False}
    ]

    result = reduce_attention_items(existing, incoming)
    assert len(result) == 3
    result_by_id = {item["id"]: item for item in result}

    # spec_ram stayed resolved: True
    assert result_by_id["spec_ram"]["resolved"] is True
    # budget item message was updated
    assert result_by_id["budget_cc-eng-001"]["message"] == "Over budget by $5,000"
    # policy item was added
    assert result_by_id["policy_vp_threshold"]["severity"] == "warning"


def test_agent_activity_reducer_append():
    """Verify reduce_agent_activity appends new actions."""
    existing = [{"tool_name": "get_inventory", "label": "Checking stock", "status": "done"}]
    incoming = [{"tool_name": "get_assets", "label": "Checking idle assets", "status": "running"}]
    
    result = reduce_agent_activity(existing, incoming)
    assert len(result) == 2
    assert result[0]["tool_name"] == "get_inventory"
    assert result[1]["tool_name"] == "get_assets"


def test_pr_artifact_reducer_and_specification_merge():
    """Verify reduce_pr_artifact merges top-level fields and runs update_specification on specs."""
    existing = {
        "item_name": "Laptop",
        "quantity": 10,
        "specifications": [
            {"field_name": "RAM", "value": "16GB", "is_confirmed": True},
            {"field_name": "Storage", "value": "512GB", "is_confirmed": True}
        ]
    }
    incoming = {
        "quantity": 8,
        "purpose": "Mobile App Development",
        "specifications": [
            # RAM changed to 32GB -> should reset is_confirmed to False
            {"field_name": "RAM", "value": "32GB"},
            # New field GPU -> added with is_confirmed=False
            {"field_name": "GPU", "value": "RTX 4080", "is_confirmed": False}
        ]
    }

    result = reduce_pr_artifact(existing, incoming)
    assert result["item_name"] == "Laptop"
    assert result["quantity"] == 8
    assert result["purpose"] == "Mobile App Development"

    specs_by_name = {s["field_name"]: s for s in result["specifications"]}
    assert len(specs_by_name) == 3
    # RAM changed, confirmed reset to False
    assert specs_by_name["RAM"]["value"] == "32GB"
    assert specs_by_name["RAM"]["is_confirmed"] is False
    # Storage remained unchanged and confirmed
    assert specs_by_name["Storage"]["value"] == "512GB"
    assert specs_by_name["Storage"]["is_confirmed"] is True
    # GPU was newly added
    assert specs_by_name["GPU"]["value"] == "RTX 4080"
    assert specs_by_name["GPU"]["is_confirmed"] is False


def test_progress_reducer():
    """Verify reduce_progress merges stage updates."""
    existing = {"clarification": "complete", "demand_analysis": "in_progress", "validation": "pending"}
    incoming = {"demand_analysis": "complete", "validation": "in_progress"}

    result = reduce_progress(existing, incoming)
    assert result["clarification"] == "complete"
    assert result["demand_analysis"] == "complete"
    assert result["validation"] == "in_progress"


def test_create_initial_graph_state():
    """Verify create_initial_graph_state helper function sets up initial Phase 1 workspace state."""
    user_context = {
        "user_id": "usr_101",
        "department_id": "DEPT-ENG",
        "cost_center": "CC-ENG-001"
    }
    state: ProcureAIState = create_initial_graph_state(user_context)
    assert state["messages"] == []
    assert state["user_context"]["user_id"] == "usr_101"
    assert state["pr"]["department"] == "DEPT-ENG"
    assert state["pr"]["cost_center"] == "CC-ENG-001"
    assert state["progress"]["clarification"] == "in_progress"
    assert state["progress"]["demand_analysis"] == "pending"
    assert state["demand"] is None
    assert state["agent_activity"] == []
    assert state["attention_items"] == []
    assert state["recommendation_status"] == "none"
    assert state["next_agent"] == "Clarification"
