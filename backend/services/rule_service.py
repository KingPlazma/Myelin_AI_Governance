"""
Custom Rule Service
Handles CRUD operations for custom rules
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import logging

from backend.config.database import get_db
from backend.config.settings import settings
from backend.models.custom_rule import CustomRuleCreate, CustomRuleUpdate

logger = logging.getLogger(__name__)


class RuleService:
    """Service for managing custom rules"""
    
    def __init__(self):
        self.db = get_db()
    
    async def create_rule(self, organization_id: str, user_id: str, 
                         rule_data: CustomRuleCreate) -> Dict[str, Any]:
        """Create a new custom rule"""
        
        # Check if organization has reached max rules limit
        existing_rules = await self.db.list_custom_rules(organization_id)
        if len(existing_rules) >= settings.MAX_CUSTOM_RULES_PER_ORG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of custom rules ({settings.MAX_CUSTOM_RULES_PER_ORG}) reached"
            )
        
        # Check if rule_id already exists for this organization
        existing_rule = await self.db.get_custom_rule(rule_data.rule_id, organization_id)
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rule with ID '{rule_data.rule_id}' already exists"
            )
        
        # Validate rule configuration based on rule type
        self._validate_rule_config(rule_data.rule_type, rule_data.rule_config)
        
        # Prepare rule data
        rule_dict = rule_data.model_dump()
        rule_dict["created_by"] = user_id
        
        # Create rule
        rule = await self.db.create_custom_rule(organization_id, rule_dict)
        
        logger.info(f"✅ Custom rule created: {rule_data.rule_id} for org {organization_id}")
        
        return rule
    
    async def get_rule(self, rule_id: str, organization_id: str) -> Dict[str, Any]:
        """Get a custom rule by ID"""
        rule = await self.db.get_custom_rule(rule_id, organization_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule '{rule_id}' not found"
            )
        return rule
    
    async def list_rules(self, organization_id: str, pillar: Optional[str] = None,
                        is_active: Optional[bool] = True) -> List[Dict[str, Any]]:
        """List all custom rules for an organization"""
        rules = await self.db.list_custom_rules(organization_id, pillar, is_active)
        return rules
    
    async def update_rule(self, rule_id: str, organization_id: str,
                         update_data: CustomRuleUpdate) -> Dict[str, Any]:
        """Update a custom rule"""
        
        # Check if rule exists
        existing_rule = await self.db.get_custom_rule(rule_id, organization_id)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule '{rule_id}' not found"
            )
        
        # Validate rule configuration if provided
        if update_data.rule_config:
            rule_type = existing_rule["rule_type"]
            self._validate_rule_config(rule_type, update_data.rule_config)
        
        # Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = "now()"
        
        # Update rule
        updated_rule = await self.db.update_custom_rule(rule_id, organization_id, update_dict)
        
        logger.info(f"✅ Custom rule updated: {rule_id} for org {organization_id}")
        
        return updated_rule
    
    async def delete_rule(self, rule_id: str, organization_id: str):
        """Delete a custom rule"""
        
        # Check if rule exists
        existing_rule = await self.db.get_custom_rule(rule_id, organization_id)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule '{rule_id}' not found"
            )
        
        # Delete rule
        await self.db.delete_custom_rule(rule_id, organization_id)
        
        logger.info(f"✅ Custom rule deleted: {rule_id} for org {organization_id}")
    
    def _validate_rule_config(self, rule_type: str, rule_config: Dict[str, Any]):
        """Validate rule configuration based on rule type"""
        
        if rule_type == "keyword":
            if "keywords" not in rule_config or not rule_config["keywords"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Keyword rules must have at least one keyword"
                )
            if not isinstance(rule_config["keywords"], list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Keywords must be a list"
                )
        
        elif rule_type == "regex":
            if "patterns" not in rule_config or not rule_config["patterns"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Regex rules must have at least one pattern"
                )
            if not isinstance(rule_config["patterns"], list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patterns must be a list"
                )
        
        elif rule_type == "llm":
            if "prompt_template" not in rule_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LLM rules must have a prompt_template"
                )
        
        # Custom rules can have any configuration
        elif rule_type == "custom":
            pass


# Global rule service instance
rule_service = RuleService()


def get_rule_service() -> RuleService:
    """Get rule service instance"""
    return rule_service
