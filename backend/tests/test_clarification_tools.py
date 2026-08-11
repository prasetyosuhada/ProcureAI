import pytest
from app.tools.clarification_tools import (
    get_categories,
    get_specifications,
    get_procurement_policy,
)

def test_get_categories_direct():
    """Test get_categories function directly and via tool invoke."""
    results = get_categories.invoke({"query": "laptop"})
    assert len(results) > 0
    assert results[0]["category_id"] == "IT-HW-01"
    assert "IT Equipment > Laptops" in results[0]["category_name"]

def test_get_categories_fallback():
    """Test get_categories fallback when no keyword matches."""
    results = get_categories.invoke({"query": "unusual item XYZ"})
    assert len(results) == 1
    assert results[0]["category_id"] == "GEN-SUPPLY"

def test_get_specifications_laptops():
    """Test get_specifications tool for IT-HW-01 laptops."""
    spec_data = get_specifications.invoke({"category_id": "IT-HW-01", "item_name": "Laptop"})
    assert "standard_models" in spec_data
    assert len(spec_data["standard_models"]) == 2
    dev_model = spec_data["standard_models"][0]
    assert dev_model["model_name"] == "Standard Developer Laptop"
    assert dev_model["specs"]["ram"] == "32GB"

def test_get_procurement_policy_laptop():
    """Test get_procurement_policy for laptops with high estimated value."""
    policy = get_procurement_policy.invoke({"item_name": "laptop", "estimated_value": 6000.0})
    assert policy["item"] == "laptop"
    assert policy["requires_it_approval"] is True
    assert "High-value purchase restriction" in policy["policy_text"]

def test_langchain_tool_metadata():
    """Verify tool metadata for LangChain agent compatibility."""
    assert get_categories.name == "get_categories"
    assert "procurement categories" in get_categories.description
    assert get_specifications.name == "get_specifications"
    assert get_procurement_policy.name == "get_procurement_policy"
