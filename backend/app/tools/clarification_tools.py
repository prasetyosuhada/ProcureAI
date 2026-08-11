from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

# Mock Data Store for Procurement Categories
MOCK_CATEGORIES = [
    {"category_id": "IT-HW-01", "category_name": "IT Equipment > Laptops", "keywords": ["laptop", "notebook", "macbook", "computer"]},
    {"category_id": "IT-HW-02", "category_name": "IT Equipment > Monitors", "keywords": ["monitor", "display", "screen"]},
    {"category_id": "IT-HW-03", "category_name": "IT Equipment > Peripherals", "keywords": ["keyboard", "mouse", "dock", "hub", "adapter"]},
    {"category_id": "OF-FURN-01", "category_name": "Office Furniture > Ergonomic Chairs", "keywords": ["chair", "seating", "desk chair"]},
    {"category_id": "OF-FURN-02", "category_name": "Office Furniture > Desks", "keywords": ["desk", "table", "standing desk"]},
    {"category_id": "SW-LIC-01", "category_name": "Software > Developer Tools", "keywords": ["ide", "software", "license", "jetbrains", "docker"]},
]

# Mock Data Store for Standard Specifications
MOCK_SPECS = {
    "IT-HW-01": {
        "standard_models": [
            {
                "model_name": "Standard Developer Laptop",
                "recommended_for": ["Backend Developer", "Frontend Developer", "Data Engineer", "DevOps"],
                "specs": {
                    "processor": "Intel i7 / Apple M-series Pro",
                    "ram": "32GB",
                    "storage": "1TB SSD",
                    "os": "macOS / Linux / Windows 11 Pro"
                }
            },
            {
                "model_name": "Standard Business Laptop",
                "recommended_for": ["General Staff", "Finance", "HR", "Sales", "Operations"],
                "specs": {
                    "processor": "Intel i5 / Apple M-series Base",
                    "ram": "16GB",
                    "storage": "512GB SSD",
                    "os": "Windows 11 Pro"
                }
            }
        ]
    },
    "IT-HW-02": {
        "standard_models": [
            {
                "model_name": "Standard 27-inch 4K Monitor",
                "recommended_for": ["Designer", "Developer", "General"],
                "specs": {
                    "resolution": "3840x2160 (4K)",
                    "size": "27 inch",
                    "connectivity": "USB-C with Power Delivery, HDMI, DisplayPort"
                }
            }
        ]
    },
    "OF-FURN-01": {
        "standard_models": [
            {
                "model_name": "Ergonomic Mesh Task Chair",
                "recommended_for": ["All Employees"],
                "specs": {
                    "lumbar_support": "Adjustable",
                    "armrests": "3D Adjustable",
                    "weight_capacity": "136 kg"
                }
            }
        ]
    }
}

# Mock Data Store for Procurement Policies
MOCK_POLICIES = {
    "laptop": "All IT hardware requests require IT Department validation. Standard developer laptops are configured with 32GB RAM for local Docker execution. Purchase value above $2,000 requires VP/Department Head approval.",
    "monitor": "Maximum 2 external monitors allowed per employee. Standard specification is 27-inch 4K USB-C.",
    "chair": "Ergonomic furniture requests must be fulfilled from existing warehouse assets if available. Purchases require Facilities approval.",
    "general": "All purchase requisitions must be justified with a business purpose and target completion date. Orders above $5,000 require competitive finance review."
}


@tool
def get_categories(query: str) -> List[Dict[str, str]]:
    """
    Look up standard enterprise procurement categories matching a search query.
    
    Args:
        query: Natural language query of the requested item (e.g. 'laptop', 'monitor', 'ergonomic chair').
        
    Returns:
        List of matching procurement categories with category_id and category_name.
    """
    query_lower = query.lower().strip()
    results = []
    
    for cat in MOCK_CATEGORIES:
        if any(kw in query_lower for kw in cat["keywords"]) or query_lower in cat["category_name"].lower():
            results.append({
                "category_id": cat["category_id"],
                "category_name": cat["category_name"]
            })
            
    if not results:
        # Fallback to general category if query is vague
        results.append({
            "category_id": "GEN-SUPPLY",
            "category_name": "General Office & IT Supplies"
        })
        
    return results


@tool
def get_specifications(category_id: str, item_name: str) -> Dict[str, Any]:
    """
    Retrieve company-approved standard models and specifications for a given category and item.
    
    Args:
        category_id: Standard procurement category ID (e.g. 'IT-HW-01').
        item_name: Name of the requested item (e.g. 'Laptop').
        
    Returns:
        Dictionary containing company-standard models, target user roles, and hardware specs.
    """
    category_specs = MOCK_SPECS.get(category_id)
    
    if category_specs:
        return category_specs
    
    # Generic specification fallback
    return {
        "standard_models": [
            {
                "model_name": f"Standard {item_name.title()}",
                "recommended_for": ["General Use"],
                "specs": {
                    "grade": "Commercial Standard",
                    "warranty": "3 Year On-Site"
                }
            }
        ]
    }


@tool
def get_procurement_policy(item_name: str, estimated_value: Optional[float] = None) -> Dict[str, Any]:
    """
    Retrieve organizational procurement policies and approval rules relevant to an item or estimated purchase value.
    
    Args:
        item_name: Name of the item being requested (e.g. 'laptop', 'chair').
        estimated_value: Optional total estimated purchase amount in USD.
        
    Returns:
        Dictionary containing human-readable policy text and threshold rules.
    """
    item_lower = item_name.lower().strip()
    matched_policy = MOCK_POLICIES.get("general")
    
    for key, policy in MOCK_POLICIES.items():
        if key in item_lower:
            matched_policy = policy
            break
            
    value_note = ""
    if estimated_value is not None:
        if estimated_value > 5000:
            value_note = " High-value purchase restriction: Requires Finance Director approval for orders over $5,000."
        elif estimated_value > 2000:
            value_note = " Mid-value purchase restriction: Requires Department Head approval for orders over $2,000."
            
    return {
        "item": item_name,
        "policy_text": f"{matched_policy}{value_note}",
        "requires_it_approval": "laptop" in item_lower or "monitor" in item_lower,
        "requires_facilities_approval": "chair" in item_lower or "desk" in item_lower
    }
