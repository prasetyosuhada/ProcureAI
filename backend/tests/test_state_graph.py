import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import create_initial_graph_state
from app.agent.graph import build_procure_graph

@pytest.mark.asyncio
async def test_build_procure_graph_compilation():
    """Verify build_procure_graph builds a compilable StateGraph instance."""
    checkpointer = MemorySaver()
    app = build_procure_graph(checkpointer=checkpointer)
    assert app is not None
    assert hasattr(app, "ainvoke")

@pytest.mark.asyncio
async def test_clarification_loop_state_machine():
    """Verify graph handles multi-turn clarification and advances when requirements are complete and confirmed."""
    checkpointer = MemorySaver()
    app = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-thread-state-machine-01"}}

    # Turn 1: Incomplete requirement (item only) -> Stays in Clarification
    user_context = {"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"}
    initial_state = create_initial_graph_state(user_context)
    initial_state["messages"] = [HumanMessage(content="I need laptops for engineers")]

    r1 = await app.ainvoke(initial_state, config=config)
    assert r1["next_agent"] == "Clarification"
    assert r1["requirement_draft"]["is_complete"] is False

    # Turn 2: User provides quantity, date, purpose -> requirement is complete, pauses for confirmation
    second_input = {"messages": [HumanMessage(content="We need 10 laptops for backend development before Sept 1")]}
    r2 = await app.ainvoke(second_input, config=config)
    assert r2["next_agent"] == "Clarification"
    assert r2["requirement_draft"]["is_complete"] is True
    assert r2["requirement_draft"]["quantity"] == 10

    # Turn 3: User explicitly confirms via confirmation_action=True -> transitions to Demand Analysis
    third_input = {
        "messages": [HumanMessage(content="I confirm the extracted specifications and requirements. Please proceed to demand analysis.")],
        "confirmation_action": True
    }
    r3 = await app.ainvoke(third_input, config=config)
    assert r3["next_agent"] == "GeneratePR"
    assert r3["demand_analysis"]["is_complete"] is True
    assert r3["demand_analysis"]["recommended_quantity"] == 2

@pytest.mark.asyncio
async def test_single_turn_complete_state_machine():
    """Verify complete single-turn input collects all details, pauses for confirmation, and executes demand analysis upon explicit confirm action."""
    checkpointer = MemorySaver()
    app = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-thread-single-turn-02"}}

    user_context = {"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"}
    initial_state = create_initial_graph_state(user_context)
    initial_state["messages"] = [
        HumanMessage(content="I need 10 laptops for backend development team before Sept 1 with 32GB RAM and 1TB SSD")
    ]

    # Turn 1: Clarification collects details and pauses for human confirmation
    r1 = await app.ainvoke(initial_state, config=config)
    assert r1["requirement_draft"]["is_complete"] is True
    assert r1["requirement_draft"]["quantity"] == 10
    assert r1["next_agent"] == "Clarification"

    # Turn 2: User explicitly confirms specifications via confirmation_action=True -> triggers Demand Analysis
    confirm_state = {
        "messages": [HumanMessage(content="I confirm the specifications. Please proceed to demand analysis.")],
        "confirmation_action": True
    }
    r2 = await app.ainvoke(confirm_state, config=config)

    assert r2["demand_analysis"]["is_complete"] is True
    assert r2["demand_analysis"]["recommended_quantity"] == 2  # 10 requested - (3 inv + 5 assets) = 2
    assert r2["next_agent"] == "GeneratePR"
