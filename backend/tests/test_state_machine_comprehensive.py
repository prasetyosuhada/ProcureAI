import pytest
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END

from app.agent.state import (
    create_initial_graph_state,
    RequirementDraftSchema,
    DemandAnalysisSchema,
    GraphState,
)
from app.agent.graph import (
    build_procure_graph,
    route_clarification,
    route_demand,
)

def test_route_clarification_edges():
    """Verify route_clarification conditional edge correctly determines next step."""
    # Case 1: Incomplete requirement -> Should route to END (wait for human response)
    incomplete_state_dict: GraphState = {
        "messages": [],
        "user_context": {},
        "requirement_draft": {"item": "Laptop", "is_complete": False},
        "demand_analysis": None,
        "pr_draft": None,
        "next_agent": "Clarification"
    }
    assert route_clarification(incomplete_state_dict) == END

    # Case 2: Complete requirement pending user confirmation -> Should pause at END
    pending_confirm_state: GraphState = {
        "messages": [],
        "user_context": {},
        "requirement_draft": {"item": "Laptop", "quantity": 10, "is_complete": True},
        "demand_analysis": None,
        "pr_draft": None,
        "next_agent": "Clarification"
    }
    assert route_clarification(pending_confirm_state) == END

    # Case 3: Confirmed requirement -> Should route to demand node
    confirmed_state: GraphState = {
        "messages": [],
        "user_context": {},
        "requirement_draft": {"item": "Monitor", "quantity": 2, "is_complete": True},
        "demand_analysis": None,
        "pr_draft": None,
        "next_agent": "Demand"
    }
    assert route_clarification(confirmed_state) == "demand"

def test_route_demand_edges():
    """Verify route_demand routes to END state upon completion."""
    completed_demand_state: GraphState = {
        "messages": [],
        "user_context": {},
        "requirement_draft": {"item": "Laptop", "quantity": 10, "is_complete": True},
        "demand_analysis": {"is_complete": True, "recommended_quantity": 2},
        "pr_draft": None,
        "next_agent": "GeneratePR"
    }
    assert route_demand(completed_demand_state) == END

@pytest.mark.asyncio
async def test_state_machine_single_turn_fast_path():
    """Verify state machine processes complete specifications, pauses for confirmation, and executes demand analysis upon confirm."""
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-fast-path-001"}}

    user_context = {
        "user_id": "usr_dev_01",
        "department_id": "DEPT-ENG",
        "cost_center": "CC-ENG-001"
    }

    initial_state = create_initial_graph_state(user_context)
    initial_state["messages"] = [
        HumanMessage(content="I need 10 laptops for backend development before Sept 1 with 32GB RAM and 1TB SSD")
    ]

    # Turn 1: Collects specifications into complete draft and pauses for confirmation
    r1 = await graph.ainvoke(initial_state, config=config)
    assert r1["requirement_draft"]["is_complete"] is True
    assert r1["requirement_draft"]["item"] == "Laptop"
    assert r1["requirement_draft"]["quantity"] == 10
    assert r1["next_agent"] == "Clarification"

    # Turn 2: User confirms -> triggers Demand Analysis
    confirm_state = {"messages": [HumanMessage(content="I confirm the specifications. Please proceed to demand analysis.")]}
    r2 = await graph.ainvoke(confirm_state, config=config)

    assert r2["demand_analysis"] is not None
    assert r2["demand_analysis"]["is_complete"] is True
    assert r2["demand_analysis"]["recommended_quantity"] == 2
    assert r2["next_agent"] == "GeneratePR"

@pytest.mark.asyncio
async def test_state_machine_multi_turn_clarification_loop():
    """Verify state machine loops on clarification until all required data is gathered and confirmed."""
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-clarification-loop-002"}}

    user_context = {
        "user_id": "usr_dev_02",
        "department_id": "DEPT-ENG",
        "cost_center": "CC-ENG-001"
    }

    # Turn 1: Vague item name only
    t1_state = create_initial_graph_state(user_context)
    t1_state["messages"] = [HumanMessage(content="I need chairs")]
    r1 = await graph.ainvoke(t1_state, config=config)

    assert r1["requirement_draft"]["is_complete"] is False
    assert r1["next_agent"] == "Clarification"
    assert r1["demand_analysis"]["is_complete"] is False

    # Turn 2: User provides quantity and team purpose -> draft is complete, pauses for confirmation
    t2_state = {"messages": [HumanMessage(content="We need 12 chairs for the operations room before Oct 15")]}
    r2 = await graph.ainvoke(t2_state, config=config)

    assert r2["requirement_draft"]["is_complete"] is True
    assert r2["requirement_draft"]["quantity"] == 12
    assert r2["next_agent"] == "Clarification"

    # Turn 3: User confirms -> triggers Demand Analysis
    t3_state = {"messages": [HumanMessage(content="I confirm the specifications. Please proceed to demand analysis.")]}
    r3 = await graph.ainvoke(t3_state, config=config)

    assert r3["demand_analysis"]["is_complete"] is True
    # 12 requested - 4 warehouse chairs - 4 unused assets = 4 recommended
    assert r3["demand_analysis"]["recommended_quantity"] == 4
    assert r3["next_agent"] == "GeneratePR"

@pytest.mark.asyncio
async def test_state_machine_human_override_resumption():
    """Verify state machine can accept direct state overrides and resume to demand analysis."""
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-override-resumption-003"}}

    user_context = {
        "user_id": "usr_lead_03",
        "department_id": "DEPT-ENG",
        "cost_center": "CC-ENG-001"
    }

    # Turn 1: Partial state
    t1_state = create_initial_graph_state(user_context)
    t1_state["messages"] = [HumanMessage(content="We need monitors")]
    r1 = await graph.ainvoke(t1_state, config=config)
    assert r1["requirement_draft"]["is_complete"] is False

    # Turn 2: State override from UI widget
    override_draft = {
        "item": "Monitor",
        "category": "IT Equipment > Monitors",
        "quantity": 6,
        "purpose": "Designers 4K Workstation",
        "required_date": "2026-09-15",
        "specifications": {"resolution": "3840x2160"},
        "is_complete": True
    }
    t2_state = {
        "messages": [HumanMessage(content="I confirm these specifications")],
        "requirement_draft": override_draft
    }
    r2 = await graph.ainvoke(t2_state, config=config)

    assert r2["requirement_draft"]["quantity"] == 6
    assert r2["requirement_draft"]["is_complete"] is True
    assert r2["demand_analysis"]["is_complete"] is True
    # 6 requested - 2 warehouse monitors - 3 unused assets = 1 recommended buy
    assert r2["demand_analysis"]["recommended_quantity"] == 1
    assert r2["next_agent"] == "GeneratePR"

@pytest.mark.asyncio
async def test_message_reducer_history_accumulation():
    """Verify add_messages reducer preserves chronological history across multiple turns."""
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-reducer-history-004"}}

    user_context = {"user_id": "usr_01", "department_id": "DEPT-ENG", "cost_center": "CC-ENG-001"}

    # Turn 1
    s1 = create_initial_graph_state(user_context)
    s1["messages"] = [HumanMessage(content="Hello, I need laptops")]
    r1 = await graph.ainvoke(s1, config=config)
    assert len(r1["messages"]) == 2  # 1 User + 1 AI

    # Turn 2
    s2 = {"messages": [HumanMessage(content="How many are in stock?")]}
    r2 = await graph.ainvoke(s2, config=config)
    assert len(r2["messages"]) == 4  # 2 User + 2 AI

    # Turn 3
    s3 = {"messages": [HumanMessage(content="We need 10 units before Sept 1 for developers")]}
    r3 = await graph.ainvoke(s3, config=config)
    assert len(r3["messages"]) >= 6  # Cumulative history preserved
