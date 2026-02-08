"""
Custom Rules API Endpoints
Handles CRUD operations for custom rules
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Optional

from backend.models.custom_rule import (
    CustomRuleCreate, CustomRuleUpdate, CustomRuleResponse,
    CustomRuleTestRequest, CustomRuleTestResponse
)
from backend.services.rule_service import get_rule_service
from backend.services.rule_engine import get_rule_engine
from backend.middleware.auth_middleware import validate_api_key

router = APIRouter(prefix="/rules", tags=["Custom Rules"])


# ============================================================================
# CUSTOM RULES CRUD ENDPOINTS
# ============================================================================

@router.post("/custom", response_model=CustomRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_rule(
    rule_data: CustomRuleCreate,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Create a new custom rule
    
    Custom rules are executed alongside default rules during audits.
    Rule IDs must follow the format: CUSTOM-{ORG}-{NUMBER} (e.g., CUSTOM-ACME-001)
    """
    rule_service = get_rule_service()
    rule_engine = get_rule_engine()
    
    organization = auth_context["organization"]
    user = auth_context["user"]
    
    rule = await rule_service.create_rule(
        organization_id=organization["id"],
        user_id=user["id"],
        rule_data=rule_data
    )
    
    # Invalidate cache
    rule_engine.invalidate_cache(organization["id"])
    
    return CustomRuleResponse(**rule)


@router.get("/custom", response_model=List[CustomRuleResponse])
async def list_custom_rules(
    pillar: Optional[str] = None,
    is_active: Optional[bool] = True,
    request: Request = None,
    auth_context = Depends(validate_api_key)
):
    """
    List all custom rules for the organization
    
    Optionally filter by pillar and active status.
    """
    rule_service = get_rule_service()
    organization = auth_context["organization"]
    
    rules = await rule_service.list_rules(
        organization_id=organization["id"],
        pillar=pillar,
        is_active=is_active
    )
    
    return [CustomRuleResponse(**rule) for rule in rules]


@router.get("/custom/{rule_id}", response_model=CustomRuleResponse)
async def get_custom_rule(
    rule_id: str,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Get a specific custom rule by ID
    """
    rule_service = get_rule_service()
    organization = auth_context["organization"]
    
    rule = await rule_service.get_rule(rule_id, organization["id"])
    
    return CustomRuleResponse(**rule)


@router.put("/custom/{rule_id}", response_model=CustomRuleResponse)
async def update_custom_rule(
    rule_id: str,
    update_data: CustomRuleUpdate,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Update a custom rule
    """
    rule_service = get_rule_service()
    rule_engine = get_rule_engine()
    organization = auth_context["organization"]
    
    rule = await rule_service.update_rule(
        rule_id=rule_id,
        organization_id=organization["id"],
        update_data=update_data
    )
    
    # Invalidate cache
    rule_engine.invalidate_cache(organization["id"])
    
    return CustomRuleResponse(**rule)


@router.delete("/custom/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_rule(
    rule_id: str,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Delete a custom rule
    """
    rule_service = get_rule_service()
    rule_engine = get_rule_engine()
    organization = auth_context["organization"]
    
    await rule_service.delete_rule(rule_id, organization["id"])
    
    # Invalidate cache
    rule_engine.invalidate_cache(organization["id"])


# ============================================================================
# RULE TESTING ENDPOINT
# ============================================================================

@router.post("/custom/test", response_model=CustomRuleTestResponse)
async def test_custom_rule(
    test_data: CustomRuleTestRequest,
    request: Request,
    auth_context = Depends(validate_api_key)
):
    """
    Test a custom rule before saving
    
    Allows you to validate rule logic with sample input/output.
    """
    rule_engine = get_rule_engine()
    
    # Create a temporary rule object
    temp_rule = {
        "rule_id": "TEST-RULE",
        "name": "Test Rule",
        "rule_type": test_data.rule_type,
        "rule_config": test_data.rule_config,
        "severity": "MEDIUM",
        "weight": 1.0
    }
    
    # Execute the rule
    result = rule_engine.execute_custom_rule(
        rule=temp_rule,
        user_input=test_data.test_input,
        bot_response=test_data.test_response
    )
    
    return CustomRuleTestResponse(
        violation=result.get("violation", False),
        reason=result.get("reason"),
        confidence=result.get("confidence"),
        trigger_span=result.get("trigger_span")
    )


# ============================================================================
# RULE TEMPLATES ENDPOINT
# ============================================================================

@router.get("/templates", response_model=List[dict])
async def list_rule_templates(
    pillar: Optional[str] = None,
    request: Request = None,
    auth_context = Depends(validate_api_key)
):
    """
    List available rule templates
    
    Templates provide pre-configured rule examples that can be customized.
    """
    from backend.config.database import get_db
    db = get_db()
    
    templates = await db.list_rule_templates(pillar)
    
    return templates
