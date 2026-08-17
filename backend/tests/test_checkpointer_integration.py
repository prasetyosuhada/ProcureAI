import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import create_initial_graph_state
from app.agent.graph import build_procure_graph

@pytest.mark.asyncio
async def test_checkpointer_preserves_conversation_history():
    """Verify checkpointer preserves full message history across sequential turns."""
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-chk-test-01"}}

    # Turn 1: Initial vague prompt
    user_context = {"user_id": "usr_01", "department_id": "DEPT-ENG", "cost_center": "CC-ENG-001"}
    s1 = create_initial_graph_state(user_context)
    s1["messages"] = [HumanMessage(content="Need laptops for engineers")]

    r1 = await graph.ainvoke(s1, config=config)
    assert r1["next_agent"] == "Clarification"
    assert len(r1["messages"]) == 2  # 1 Human + 1 AI

    # Turn 2: Follow-up clarification response in same thread
    s2 = {"messages": [HumanMessage(content="We need 10 units before Sept 1 for backend team with 32GB RAM and 1TB SSD")]}
    r2 = await graph.ainvoke(s2, config=config)
    
    # State should have preserved previous item and merged new details
    assert r2["requirement_draft"]["is_complete"] is True
    assert r2["requirement_draft"]["quantity"] == 10
    assert r2["demand_analysis"]["is_complete"] is True
    assert r2["demand_analysis"]["recommended_quantity"] == 2
    assert len(r2["messages"]) >= 4  # Preserved history across turns

@pytest.mark.asyncio
async def test_checkpointer_isolates_different_threads():
    """Verify checkpointer maintains separate state isolation between different thread IDs."""
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    
    config_a = {"configurable": {"thread_id": "thread-user-A"}}
    config_b = {"configurable": {"thread_id": "thread-user-B"}}

    user_context = {"user_id": "usr_01", "department_id": "DEPT-ENG", "cost_center": "CC-ENG-001"}
    
    # Thread A asks for monitors
    sa = create_initial_graph_state(user_context)
    sa["messages"] = [HumanMessage(content="I need 5 monitors for marketing team before Sept 1")]
    ra = await graph.ainvoke(sa, config=config_a)

    # Thread B asks for chairs
    sb = create_initial_graph_state(user_context)
    sb["messages"] = [HumanMessage(content="I need 20 ergonomic chairs for operations before Sept 1")]
    rb = await graph.ainvoke(sb, config=config_b)

    assert ra["requirement_draft"]["item"] == "Monitor"
    assert rb["requirement_draft"]["item"] == "Ergonomic Chair"
    assert ra["requirement_draft"]["quantity"] == 5
    assert rb["requirement_draft"]["quantity"] == 20
