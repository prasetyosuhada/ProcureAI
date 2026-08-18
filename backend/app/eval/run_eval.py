import asyncio
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from app.agent.graph import build_procure_graph
from app.agent.state import create_initial_graph_state
from app.eval.dataset import GOLDEN_DATASET
from app.eval.evaluator import evaluate_with_llm_judge

async def run_evaluation_suite():
    """
    Executes the full evaluation suite on the 5 Golden Dataset scenarios.
    """
    print("\n" + "="*80)
    print("🚀 PROCUREAI AUTOMATED EVALUATION SUITE (LLM-AS-A-JUDGE & DETERMINISTIC)")
    print("="*80 + "\n")

    checkpointer = MemorySaver()
    graph = build_procure_graph(checkpointer=checkpointer)
    results = []

    for idx, scenario in enumerate(GOLDEN_DATASET, 1):
        print(f"[{idx}/5] Evaluating: {scenario.name} ({scenario.id})...")
        config = {"configurable": {"thread_id": f"eval_thread_{scenario.id}"}}

        input_state = create_initial_graph_state(scenario.user_context)
        input_state["messages"] = [HumanMessage(content=scenario.user_input)]

        output_state = await graph.ainvoke(input_state, config=config)

        # Extract last AI message content
        ai_text = ""
        for msg in reversed(output_state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                ai_text = str(msg.content)
                break
            elif hasattr(msg, "content"):
                ai_text = str(msg.content)
                break

        judge_res = await evaluate_with_llm_judge(scenario, ai_text, output_state)
        results.append(judge_res)

        status_emoji = "✅ PASS" if judge_res.passed else "❌ FAIL"
        print(f"      Result: {status_emoji} | Score: {judge_res.score:.2f} | Reason: {judge_res.reasoning}\n")

    # Generate Markdown Summary Report
    print("\n" + "="*80)
    print("📊 EVALUATION REPORT SUMMARY")
    print("="*80)

    total_scenarios = len(results)
    passed_count = sum(1 for r in results if r.passed)
    pass_rate = (passed_count / total_scenarios) * 100

    print(f"\nOverall Pass Rate: {passed_count}/{total_scenarios} ({pass_rate:.1f}%)\n")
    print("| Scenario ID | Scenario Name | Status | Score | Extraction | Math | Guardrail |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        status_str = "✅ PASS" if r.passed else "❌ FAIL"
        ext_str = "✅" if r.metrics.get("item_extraction_accurate") else "❌"
        math_str = "✅" if r.metrics.get("math_accurate") else "❌"
        gr_str = "✅" if r.metrics.get("guardrail_complied") else "❌"
        print(f"| `{r.scenario_id}` | {r.scenario_name} | {status_str} | {r.score:.2f} | {ext_str} | {math_str} | {gr_str} |")

    print("\n" + "="*80)

    return results

if __name__ == "__main__":
    asyncio.run(run_evaluation_suite())
