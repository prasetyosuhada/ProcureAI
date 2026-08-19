import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from app.agent.graph import build_procure_graph
from app.eval.dataset import GOLDEN_DATASET, GoldenScenario
from app.eval.evaluator import evaluate_with_llm_judge

@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", GOLDEN_DATASET, ids=[s.id for s in GOLDEN_DATASET])
async def test_golden_scenario_evaluation(scenario: GoldenScenario):
    """
    Evaluates each Golden Dataset scenario through the LangGraph agent and asserts that it passes all evaluation rubrics.
    """
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": f"test_thread_{scenario.id}"}}

    input_state = {
        "messages": [HumanMessage(content=scenario.user_input)],
        "user_context": scenario.user_context
    }

    output_state = await graph.ainvoke(input_state, config=config)

    # If requirement draft is complete and scenario expects demand evaluation, simulate human confirmation
    if output_state.get("requirement_draft", {}).get("is_complete") and scenario.expected_recommended_quantity is not None and not output_state.get("demand_analysis", {}).get("is_complete"):
        confirm_input = {"messages": [HumanMessage(content="I confirm the extracted specifications and requirements. Please proceed to demand analysis.")]}
        output_state = await graph.ainvoke(confirm_input, config=config)

    # Extract last AI message content
    ai_text = ""
    for msg in reversed(output_state.get("messages", [])):
        if hasattr(msg, "type") and msg.type == "ai":
            ai_text = str(msg.content)
            break
        elif hasattr(msg, "content"):
            ai_text = str(msg.content)
            break

    judge_result = await evaluate_with_llm_judge(scenario, ai_text, output_state)

    assert judge_result.passed is True, f"Scenario {scenario.id} failed: {judge_result.reasoning} | Metrics: {judge_result.metrics}"
    assert judge_result.score == 1.0
