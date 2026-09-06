import pytest
from datetime import date
from unittest.mock import patch
from langchain_core.messages import HumanMessage
from app.agent.state import create_initial_graph_state
from app.agent.nodes.clarification_node import requirement_clarification_node, extract_requirement_heuristics

def test_extract_requirement_heuristics_incomplete():
    """Verify extraction on incomplete user request."""
    user_text = "I need laptops for my team"
    draft = extract_requirement_heuristics(user_text, {})
    assert draft["item"] == "Laptop"
    assert draft["quantity"] is None
    assert draft["is_complete"] is False

def test_extract_requirement_heuristics_complete():
    """Verify extraction on complete user request."""
    user_text = "I need 10 laptops for backend development before Sept 1 with 32GB RAM and 1TB SSD"
    draft = extract_requirement_heuristics(user_text, {}, reference_date=date(2026, 8, 1))
    assert draft["item"] == "Laptop"
    assert draft["quantity"] == 10
    assert draft["purpose"] == "Backend Development Team"
    assert draft["required_date"] == "2026-09-01"
    assert draft["specifications"]["ram"] == "32GB"
    assert draft["specifications"]["storage"] == "1TB SSD"
    assert draft["is_complete"] is True


@pytest.mark.parametrize(
    ("user_text", "today", "expected"),
    [
        ("Need laptops next week", date(2026, 9, 6), "2026-09-13"),
        ("Need laptops next month", date(2026, 1, 31), "2026-02-28"),
        ("Need laptops before Sept 15", date(2026, 9, 6), "2026-09-15"),
        ("Need laptops before Sept 1", date(2026, 9, 6), "2027-09-01"),
    ],
)
def test_extract_requirement_dates_use_runtime_date(user_text, today, expected):
    draft = extract_requirement_heuristics(user_text, {}, reference_date=today)
    assert draft["required_date"] == expected


@pytest.mark.asyncio
async def test_current_date_question_uses_backend_clock_without_mutating_draft():
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    original_draft = dict(state["requirement_draft"])
    state["messages"] = [HumanMessage(content="tanggal berapa hari ini?")]

    with patch(
        "app.agent.nodes.clarification_node.get_business_today",
        return_value=date(2026, 9, 6),
    ), patch("app.agent.nodes.clarification_node.ChatGoogleGenerativeAI") as mock_llm:
        result = await requirement_clarification_node(state)

    assert result["messages"][0].content == "Hari ini tanggal 6 September 2026 (Asia/Jakarta)."
    assert result["next_agent"] == "Clarification"
    assert state["requirement_draft"] == original_draft
    assert "requirement_draft" not in result
    mock_llm.assert_not_called()

@pytest.mark.asyncio
async def test_clarification_node_incomplete():
    """Verify requirement_clarification_node response when requirement is incomplete."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [HumanMessage(content="We need monitors for design team")]
    
    result = await requirement_clarification_node(state)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["next_agent"] == "Clarification"
    assert result["requirement_draft"]["is_complete"] is False
    assert result["pr"]["is_ready_for_confirmation"] is False

@pytest.mark.asyncio
async def test_clarification_node_complete():
    """Verify requirement_clarification_node response when requirement details are complete (pending user confirmation)."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [
        HumanMessage(content="I need 10 laptops for backend development before September 1")
    ]
    
    result = await requirement_clarification_node(state)
    assert result["next_agent"] == "Clarification"
    assert result["requirement_draft"]["is_complete"] is True
    assert result["requirement_draft"]["quantity"] == 10
    assert result["pr"]["is_ready_for_confirmation"] is True
    assert "confirm" in result["messages"][0].content.lower() or "summary" in result["messages"][0].content.lower() or "demand" in result["messages"][0].content.lower()


@pytest.mark.asyncio
async def test_clarification_node_ram_policy_uses_tool_contract():
    """RAM policy validation passes item_name expected by get_procurement_policy."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [
        HumanMessage(content="I need 10 laptops for backend development before September 1 with 32GB RAM")
    ]

    with patch("app.agent.nodes.clarification_node.settings.GEMINI_API_KEY", ""), \
         patch("app.agent.nodes.clarification_node.get_categories") as mock_categories, \
         patch("app.agent.nodes.clarification_node.get_procurement_policy") as mock_policy:
        mock_categories.invoke.return_value = [{
            "category_id": "IT-HW-01",
            "category_name": "IT Equipment > Laptops",
        }]
        mock_policy.invoke.return_value = {
            "policy_text": "Standard policy",
            "requires_it_approval": True,
            "requires_facilities_approval": False,
        }

        result = await requirement_clarification_node(state)

    mock_policy.invoke.assert_called_once_with({"item_name": "Laptop"})
    assert result["requirement_draft"]["quantity"] == 10

@pytest.mark.asyncio
async def test_clarification_node_no_keyword_false_positive():
    """
    Verify that phrases like 'tolong sesuaikan RAM-nya jadi 16GB' do NOT cause false positive
    confirmation or premature routing to Demand.
    """
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["requirement_draft"] = {
        "item": "Laptop",
        "category": "IT Equipment > Laptops",
        "quantity": 10,
        "purpose": "Backend Development Team",
        "required_date": "2026-09-01",
        "specifications": {"ram": "32GB"},
        "is_complete": True
    }
    # User message contains 'sesuai' substring as part of 'sesuaikan'
    state["messages"] = [
        HumanMessage(content="tolong sesuaikan RAM-nya jadi 16GB")
    ]
    state["confirmation_action"] = False
    
    result = await requirement_clarification_node(state)
    # Must NOT route to Demand because confirmation_action is False
    assert result["next_agent"] == "Clarification"
    # Specifications must NOT be confirmed
    for spec in result["pr"].get("specifications", []):
        assert spec["is_confirmed"] is False

@pytest.mark.asyncio
async def test_clarification_node_explicit_action_confirm():
    """
    Verify that only the explicit boolean flag confirmation_action=True
    advances the workflow to Demand and marks specifications as confirmed.
    """
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["requirement_draft"] = {
        "item": "Laptop",
        "category": "IT Equipment > Laptops",
        "quantity": 10,
        "purpose": "Backend Development Team",
        "required_date": "2026-09-01",
        "specifications": {"ram": "32GB", "storage": "1TB SSD"},
        "is_complete": True
    }
    state["confirmation_action"] = True
    state["messages"] = [
        HumanMessage(content="Confirmed via UI button")
    ]
    
    result = await requirement_clarification_node(state)
    assert result["next_agent"] == "Demand"
    assert result["progress"]["clarification"] == "complete"
    assert result["progress"]["demand_analysis"] == "in_progress"
    
    # Specifications are now confirmed
    specs = result["pr"].get("specifications", [])
    assert len(specs) == 2
    for s in specs:
        assert s["is_confirmed"] is True

@pytest.mark.asyncio
async def test_clarification_node_other_item():
    """Verify requirement_clarification_node handles arbitrary items like standing desks."""
    state = create_initial_graph_state({"user_id": "usr_1", "department_id": "DEPT-ENG"})
    state["messages"] = [
        HumanMessage(content="I need 5 standing desks for UI/UX Design Team before Sept 1")
    ]
    
    result = await requirement_clarification_node(state)
    assert result["next_agent"] == "Clarification"
    assert result["requirement_draft"]["is_complete"] is True
    assert result["requirement_draft"]["item"] == "Standing Desks" or result["requirement_draft"]["item"] == "Standing Desk"
    assert result["requirement_draft"]["quantity"] == 5
    assert result["requirement_draft"]["category"] == "Office Furniture > Desks"
