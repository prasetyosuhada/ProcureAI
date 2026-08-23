import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_procure_graph
from app.eval.golden_dataset import GOLDEN_SCENARIOS, Scenario
from app.eval.evaluator import evaluate_with_llm_judge

@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", GOLDEN_SCENARIOS, ids=[s.id for s in GOLDEN_SCENARIOS])
async def test_scenario_golden_dataset_execution(scenario: Scenario):
    """
    Executes each Golden Dataset scenario against the ProcureAI LangGraph pipeline
    and asserts with the automated LLM Judge.
    """
    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": f"test_thread_{scenario.id}"}}

    input_state = {
        "messages": [HumanMessage(content=scenario.user_input)],
        "user_context": scenario.user_context
    }

    output_state = await graph.ainvoke(input_state, config=config)

    # If requirement draft is complete and scenario expects demand evaluation, simulate explicit human confirmation
    if output_state.get("requirement_draft", {}).get("is_complete") and scenario.expected_recommended_quantity is not None and not output_state.get("demand_analysis", {}).get("is_complete"):
        confirm_input = {
            "messages": [HumanMessage(content="I confirm the extracted specifications and requirements. Please proceed to demand analysis.")],
            "confirmation_action": True
        }
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

    # Assert evaluation criteria
    assert judge_result["passed"] is True, f"Scenario {scenario.id} failed eval: {judge_result['feedback']}"
    assert judge_result["field_completeness_score"] >= 0.8
    assert judge_result["spec_accuracy_score"] >= 0.8
    assert judge_result["recommendation_accuracy_score"] >= 0.8
