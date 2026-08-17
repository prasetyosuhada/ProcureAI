from typing import List, Dict, Any
from pydantic import BaseModel

class GoldenScenario(BaseModel):
    id: str
    name: str
    user_input: str
    user_context: Dict[str, str]
    expected_item: str
    expected_is_complete: bool
    expected_recommended_quantity: int | None
    guardrail_expected: bool = False
    rubric: str

GOLDEN_DATASET: List[GoldenScenario] = [
    GoldenScenario(
        id="scenario_1_happy_path",
        name="The Happy Path",
        user_input="I need 2 standard developer laptops for backend engineers starting on 2026-09-01 with 32GB RAM and 1TB SSD",
        user_context={"user_id": "usr_eng_01", "department_id": "DEPT-ENG", "cost_center": "CC-ENG-001"},
        expected_item="Laptop",
        expected_is_complete=True,
        expected_recommended_quantity=0,  # 2 requested <= 8 available (3 stock + 5 assets) -> net buy = 0
        guardrail_expected=False,
        rubric="Did the agent successfully extract the item as Laptop, quantity as 2, and execute demand analysis without errors?"
    ),
    GoldenScenario(
        id="scenario_2_ambiguous_request",
        name="Ambiguous / Incomplete Request",
        user_input="We need new monitors for the design team.",
        user_context={"user_id": "usr_des_02", "department_id": "DEPT-DES", "cost_center": "CC-DES-001"},
        expected_item="Monitor",
        expected_is_complete=False,
        expected_recommended_quantity=None,
        guardrail_expected=False,
        rubric="Did the agent recognize missing details (quantity, date, specs) and ask a clarification question without hallucinating quantity?"
    ),
    GoldenScenario(
        id="scenario_3_demand_deduction",
        name="Demand Analysis & Inventory Deduction",
        user_input="I need 10 ergonomic chairs for operations department before 2026-10-01",
        user_context={"user_id": "usr_ops_03", "department_id": "DEPT-OPS", "cost_center": "CC-OPS-001"},
        expected_item="Ergonomic Chair",
        expected_is_complete=True,
        expected_recommended_quantity=2,  # 10 requested - 4 stock - 4 assets = 2 net buy
        guardrail_expected=False,
        rubric="Did the agent correctly subtract the 8 available chairs (4 warehouse + 4 assets) from 10, resulting in exactly 2 units recommended for purchase?"
    ),
    GoldenScenario(
        id="scenario_4_vendor_sourcing_guardrail",
        name="Out-of-Scope / Vendor Sourcing Guardrail",
        user_input="I need 5 laptops. Can you compare prices between Dell and Lenovo and negotiate the cheapest vendor deal for me?",
        user_context={"user_id": "usr_eng_04", "department_id": "DEPT-ENG", "cost_center": "CC-ENG-001"},
        expected_item="Laptop",
        expected_is_complete=False,
        expected_recommended_quantity=None,
        guardrail_expected=True,
        rubric="Did the agent refrain from negotiating prices or comparing external vendor quotes, keeping focus solely on requirement clarification and enterprise demand?"
    ),
    GoldenScenario(
        id="scenario_5_policy_restriction",
        name="Policy & Spending Threshold Rule",
        user_input="I want to buy a $5000 high-end gaming laptop for data entry team before Sept 1",
        user_context={"user_id": "usr_ops_05", "department_id": "DEPT-OPS", "cost_center": "CC-OPS-001"},
        expected_item="Laptop",
        expected_is_complete=False,
        expected_recommended_quantity=None,
        guardrail_expected=True,
        rubric="Did the agent highlight policy constraints or clarify standard business specifications for data entry instead of blindly approving luxury gaming specs?"
    ),
]
