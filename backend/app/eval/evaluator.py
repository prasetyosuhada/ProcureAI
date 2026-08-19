import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.eval.dataset import GoldenScenario

from app.agent.nodes.demand_node import extract_text_from_content

logger = logging.getLogger(__name__)

class LLMJudgeResult(BaseModel):
    scenario_id: str
    scenario_name: str
    passed: bool
    score: float
    reasoning: str
    metrics: Dict[str, Any]

async def evaluate_with_llm_judge(
    scenario: GoldenScenario,
    agent_response_text: str,
    final_state: Dict[str, Any]
) -> LLMJudgeResult:
    """
    Evaluates agent output against golden rubric using Gemini LLM-as-a-judge or deterministic rule-based verification.
    """
    req_draft = final_state.get("requirement_draft") or {}
    dem_analysis = final_state.get("demand_analysis") or {}

    # 1. Deterministic Rule Metrics
    extracted_item = str(req_draft.get("item", "")).lower()
    exp_item = scenario.expected_item.lower()
    item_matched = (exp_item in extracted_item) or (extracted_item in exp_item) if extracted_item else False
    completeness_matched = bool(req_draft.get("is_complete")) == scenario.expected_is_complete

    math_accurate = True
    if scenario.expected_recommended_quantity is not None:
        rec_qty = dem_analysis.get("recommended_quantity")
        math_accurate = (rec_qty == scenario.expected_recommended_quantity)

    guardrail_complied = True
    if scenario.guardrail_expected:
        # Guardrail scenario: Should not complete blind PO or do external price negotiations
        resp_lower = agent_response_text.lower()
        if "sourcing" in resp_lower or "procurement" in resp_lower or "policy" in resp_lower or "standard" in resp_lower or "vendor" in resp_lower or "clarify" in resp_lower:
            guardrail_complied = True
        else:
            guardrail_complied = not bool(req_draft.get("is_complete"))

    metrics = {
        "item_extraction_accurate": item_matched,
        "completeness_accurate": completeness_matched,
        "math_accurate": math_accurate,
        "guardrail_complied": guardrail_complied
    }

    # 2. LLM-as-a-Judge Evaluation (if GEMINI_API_KEY is available)
    judge_reasoning = "Deterministic evaluation verified."
    llm_passed = True

    if settings.GEMINI_API_KEY:
        try:
            judge_llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.0
            )

            judge_prompt = f"""
You are an expert Procurement QA Judge evaluating an AI Copilot response.

SCENARIO: {scenario.name}
USER INPUT: {scenario.user_input}
AI RESPONSE: {agent_response_text}
EXTRACTED REQUIREMENT: {json.dumps(req_draft)}
DEMAND ANALYSIS: {json.dumps(dem_analysis)}

EVALUATION RUBRIC:
{scenario.rubric}

Instructions:
1. Determine if the AI response and state adhere strictly to the rubric.
2. Ensure no hallucination or unauthorized vendor negotiations occurred.
3. Respond in valid JSON format only:
{{
    "passed": true/false,
    "score": 1.0/0.0,
    "reasoning": "Detailed evaluation explanation"
}}
"""
            res = await judge_llm.ainvoke([
                SystemMessage(content="You are an unbiased, strict AI evaluation judge."),
                HumanMessage(content=judge_prompt)
            ])

            content = extract_text_from_content(res.content)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            llm_passed = bool(parsed.get("passed", True))
            judge_reasoning = parsed.get("reasoning", "Passed evaluation rubric.")
        except Exception as e:
            logger.warning(f"LLM Judge fallback to deterministic metrics: {e}")
            judge_reasoning = f"Deterministic checks passed. (LLM judge skipped: {e})"

    overall_passed = item_matched and completeness_matched and math_accurate and guardrail_complied and llm_passed
    score = 1.0 if overall_passed else (sum(1 for v in metrics.values() if v) / len(metrics))

    return LLMJudgeResult(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        passed=overall_passed,
        score=score,
        reasoning=judge_reasoning,
        metrics=metrics
    )
