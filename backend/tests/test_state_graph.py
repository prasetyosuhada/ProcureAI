import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import create_initial_graph_state
from app.agent.graph import build_procure_graph, route_clarification, route_demand
from langgraph.graph import END

def test_route_clarification_incomplete():
    """Verify route_clarification ends turn when requirement is incomplete."""
    state = {
        "next_agent": "Clarification",
        "requirement_draft": {"is_complete": False}
    }
    assert route_clarification(state) == END

def test_route_clarification_complete():
    """Verify route_clarification transitions to demand node when complete."""
    state = {
        "next_agent": "Demand",
        "requirement_draft": {"is_complete": True}
    }
    assert route_clarification(state) == "demand"

@pytest.mark.asyncio
async def test_state_graph_clarification_turn_with_checkpointer():
    """Verify state graph execution pauses after clarification when details are missing."""
    checkpointer = MemorySaver()
    app = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-test-1"}}

    user_context = {"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"}
    initial_state = create_initial_graph_state(user_context)
    initial_state["messages"] = [HumanMessage(content="I need laptops")]

    result = await app.ainvoke(initial_state, config=config)

    assert result["requirement_draft"]["is_complete"] is False
    assert result["next_agent"] == "Clarification"
    assert len(result["messages"]) >= 2
    # Verify state was checkpointed
    saved_state = await app.aget_state(config)
    assert saved_state.values["requirement_draft"]["item"] == "Laptop"

@pytest.mark.asyncio
async def test_state_graph_full_flow_clarification_to_demand():
    """Verify state graph executes Clarification and automatically flows into Demand node when complete."""
    checkpointer = MemorySaver()
    app = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-test-2"}}

    user_context = {"user_id": "usr_101", "cost_center": "CC-ENG-001", "department_id": "DEPT-ENG"}
    initial_state = create_initial_graph_state(user_context)
    initial_state["messages"] = [
        HumanMessage(content="I need 10 laptops for backend development team before Sept 1 with 32GB RAM and 1TB SSD")
    ]

    result = await app.ainvoke(initial_state, config=config)

    # Verify both Clarification and Demand nodes executed
    assert result["requirement_draft"]["is_complete"] is True
    assert result["requirement_draft"]["quantity"] == 10
    assert result["demand_analysis"]["is_complete"] is True
    assert result["demand_analysis"]["recommended_quantity"] == 2  # 10 requested - (3 inv + 5 assets) = 2
    assert result["next_agent"] == "GeneratePR"
