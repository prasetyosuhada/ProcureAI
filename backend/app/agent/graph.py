import logging
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import GraphState, create_initial_graph_state
from app.agent.nodes.clarification_node import requirement_clarification_node
from app.agent.nodes.demand_node import demand_analysis_node
from app.db.redis import check_redis_connection

logger = logging.getLogger(__name__)

# Module-level memory checkpointer instance for fallback & fast threads
_memory_checkpointer = MemorySaver()
_compiled_procure_graph = None

def route_clarification(state: GraphState) -> str:
    """
    Conditional routing from Clarification node.
    If requirement is complete and next_agent is Demand, proceed to Demand node.
    Otherwise, pause/end turn to wait for human user clarification input.
    """
    next_agent = state.get("next_agent")
    req_draft = state.get("requirement_draft", {})
    if next_agent == "Demand" or req_draft.get("is_complete"):
        return "demand"
    return END

def route_demand(state: GraphState) -> str:
    """
    Conditional routing from Demand node.
    Transitions to GeneratePR or ends turn.
    """
    next_agent = state.get("next_agent")
    if next_agent == "GeneratePR":
        return END
    return END

def build_procure_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    """
    Assembles the StateGraph with Clarification and Demand nodes and compiles with a checkpointer.
    """
    builder = StateGraph(GraphState)

    # 1. Add Agent Nodes
    builder.add_node("clarification", requirement_clarification_node)
    builder.add_node("demand", demand_analysis_node)

    # 2. Add Edges & Conditional Routing
    builder.add_edge(START, "clarification")
    builder.add_conditional_edges(
        "clarification",
        route_clarification,
        {
            "demand": "demand",
            END: END
        }
    )
    builder.add_conditional_edges(
        "demand",
        route_demand,
        {
            END: END
        }
    )

    # 3. Compile Graph with Checkpointer
    return builder.compile(checkpointer=checkpointer)

async def get_compiled_procure_graph():
    """
    Returns a compiled StateGraph with persistent checkpointer.
    """
    global _compiled_procure_graph
    if _compiled_procure_graph is None:
        _compiled_procure_graph = build_procure_graph(checkpointer=_memory_checkpointer)
    return _compiled_procure_graph
