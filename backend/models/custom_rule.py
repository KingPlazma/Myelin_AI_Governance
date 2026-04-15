"""
Custom Rule Models
Pydantic models for custom rule management
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RulePillar(str, Enum):
    """Rule pillar/category"""
    TOXICITY = "toxicity"
    GOVERNANCE = "governance"
    BIAS = "bias"
    FACTUAL = "factual"
    FAIRNESS = "fairness"


class RuleSeverity(str, Enum):
    """Rule severity level"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleType(str, Enum):
    """Type of rule implementation"""
    KEYWORD = "keyword"
    REGEX = "regex"
    LLM = "llm"
    CUSTOM = "custom"


class KeywordRuleConfig(BaseModel):
    """Configuration for keyword-based rules"""
    keywords: List[str] = Field(..., min_items=1, description="List of keywords to detect")
    case_sensitive: bool = Field(default=False, description="Whether matching is case-sensitive")
    whole_word_only: bool = Field(default=False, description="Match whole words only")


class RegexRuleConfig(BaseModel):
    """Configuration for regex-based rules"""
    patterns: List[str] = Field(..., min_items=1, description="List of regex patterns")
    flags: Optional[str] = Field(None, description="Regex flags (e.g., 'i' for case-insensitive)")


class LLMRuleConfig(BaseModel):
    """Configuration for LLM-based rules"""
    prompt_template: str = Field(..., description="Prompt template for LLM evaluation")
    model: str = Field(default="gpt-3.5-turbo", description="LLM model to use")
    threshold: float = Field(default=0.7, ge=0, le=1, description="Confidence threshold")


class CustomRuleBase(BaseModel):
    """Base custom rule model"""
    rule_id: str = Field(..., pattern=r"^CUSTOM-[A-Z0-9]+-\d+$", description="Unique rule ID (e.g., CUSTOM-ORG1-001)")
    pillar: RulePillar = Field(..., description="Which pillar this rule belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    category: Optional[str] = Field(None, max_length=100, description="Rule category")
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Rule severity")
    weight: float = Field(default=1.0, ge=0, le=10, description="Rule weight in scoring")
    rule_type: RuleType = Field(..., description="Type of rule implementation")
    rule_config: Dict[str, Any] = Field(..., description="Rule configuration (varies by rule_type)")
    is_active: bool = Field(default=True, description="Whether the rule is active")


class CustomRuleCreate(CustomRuleBase):
    """Model for creating a custom rule"""
    pass


class CustomRuleUpdate(BaseModel):
    """Model for updating a custom rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    severity: Optional[RuleSeverity] = None
    weight: Optional[float] = Field(None, ge=0, le=10)
    rule_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CustomRule(CustomRuleBase):
    """Complete custom rule model"""
    id: str
    organization_id: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CustomRuleResponse(BaseModel):
    """Custom rule response model"""
    id: str
    rule_id: str
    pillar: str
    name: str
    description: Optional[str]
    category: Optional[str]
    severity: str
    weight: float
    rule_type: str
    rule_config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CustomRuleTestRequest(BaseModel):
    """Model for testing a custom rule"""
    rule_type: RuleType
    rule_config: Dict[str, Any]
    test_input: str = Field(..., description="User input to test")
    test_response: str = Field(..., description="Bot response to test")


class CustomRuleTestResponse(BaseModel):
    """Response from testing a custom rule"""
    violation: bool
    reason: Optional[str]
    confidence: Optional[float]
    trigger_span: Optional[str]

