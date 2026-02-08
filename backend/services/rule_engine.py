"""
Rule Engine
Dynamically loads and executes custom rules alongside default rules
"""

from typing import List, Dict, Any, Optional
import re
import logging
from datetime import datetime, timedelta
from functools import lru_cache

from backend.config.database import get_db
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class RuleEngine:
    """Engine for loading and executing custom rules"""
    
    def __init__(self):
        self.db = get_db()
        self._rule_cache: Dict[str, tuple] = {}  # {org_id: (rules, timestamp)}
    
    async def get_custom_rules(self, organization_id: str, pillar: Optional[str] = None,
                              use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get custom rules for an organization with caching
        """
        cache_key = f"{organization_id}:{pillar or 'all'}"
        
        # Check cache
        if use_cache and cache_key in self._rule_cache:
            rules, timestamp = self._rule_cache[cache_key]
            cache_age = (datetime.utcnow() - timestamp).total_seconds()
            
            if cache_age < settings.RULE_CACHE_TTL_SECONDS:
                logger.debug(f"Using cached rules for {cache_key}")
                return rules
        
        # Fetch from database
        rules = await self.db.list_custom_rules(organization_id, pillar, is_active=True)
        
        # Update cache
        self._rule_cache[cache_key] = (rules, datetime.utcnow())
        
        logger.debug(f"Loaded {len(rules)} custom rules for org {organization_id}")
        
        return rules
    
    def invalidate_cache(self, organization_id: str):
        """Invalidate rule cache for an organization"""
        keys_to_remove = [k for k in self._rule_cache.keys() if k.startswith(organization_id)]
        for key in keys_to_remove:
            del self._rule_cache[key]
        logger.debug(f"Cache invalidated for org {organization_id}")
    
    def execute_custom_rule(self, rule: Dict[str, Any], user_input: str, 
                           bot_response: str) -> Dict[str, Any]:
        """
        Execute a single custom rule
        Returns: {violation: bool, reason: str, ...}
        """
        rule_type = rule["rule_type"]
        rule_config = rule["rule_config"]
        
        try:
            if rule_type == "keyword":
                return self._execute_keyword_rule(rule, user_input, bot_response, rule_config)
            elif rule_type == "regex":
                return self._execute_regex_rule(rule, user_input, bot_response, rule_config)
            elif rule_type == "llm":
                return self._execute_llm_rule(rule, user_input, bot_response, rule_config)
            elif rule_type == "custom":
                return self._execute_custom_rule_logic(rule, user_input, bot_response, rule_config)
            else:
                logger.warning(f"Unknown rule type: {rule_type}")
                return {"violation": False}
        
        except Exception as e:
            logger.error(f"Error executing rule {rule['rule_id']}: {e}")
            return {"violation": False, "error": str(e)}
    
    def _execute_keyword_rule(self, rule: Dict[str, Any], user_input: str,
                             bot_response: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a keyword-based rule"""
        keywords = config.get("keywords", [])
        case_sensitive = config.get("case_sensitive", False)
        whole_word_only = config.get("whole_word_only", False)
        
        # Combine input and response for checking
        text_to_check = f"{user_input} {bot_response}"
        
        if not case_sensitive:
            text_to_check = text_to_check.lower()
            keywords = [k.lower() for k in keywords]
        
        for keyword in keywords:
            if whole_word_only:
                # Use word boundary regex
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_to_check):
                    return {
                        "violation": True,
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["name"],
                        "category": rule.get("category", "custom"),
                        "severity": rule["severity"],
                        "confidence": 0.95,
                        "trigger_span": keyword,
                        "reason": f"Keyword '{keyword}' detected",
                        "weight": rule["weight"]
                    }
            else:
                if keyword in text_to_check:
                    return {
                        "violation": True,
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["name"],
                        "category": rule.get("category", "custom"),
                        "severity": rule["severity"],
                        "confidence": 0.95,
                        "trigger_span": keyword,
                        "reason": f"Keyword '{keyword}' detected",
                        "weight": rule["weight"]
                    }
        
        return {"violation": False}
    
    def _execute_regex_rule(self, rule: Dict[str, Any], user_input: str,
                           bot_response: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a regex-based rule"""
        patterns = config.get("patterns", [])
        flags_str = config.get("flags", "")
        
        # Parse regex flags
        flags = 0
        if 'i' in flags_str:
            flags |= re.IGNORECASE
        if 'm' in flags_str:
            flags |= re.MULTILINE
        if 's' in flags_str:
            flags |= re.DOTALL
        
        # Combine input and response for checking
        text_to_check = f"{user_input} {bot_response}"
        
        for pattern_str in patterns:
            try:
                pattern = re.compile(pattern_str, flags)
                match = pattern.search(text_to_check)
                
                if match:
                    return {
                        "violation": True,
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["name"],
                        "category": rule.get("category", "custom"),
                        "severity": rule["severity"],
                        "confidence": 0.90,
                        "trigger_span": match.group(0),
                        "reason": f"Pattern '{pattern_str}' matched",
                        "weight": rule["weight"]
                    }
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern_str}': {e}")
                continue
        
        return {"violation": False}
    
    def _execute_llm_rule(self, rule: Dict[str, Any], user_input: str,
                         bot_response: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an LLM-based rule"""
        # TODO: Implement LLM-based rule execution
        # This would call an LLM API with the prompt template
        logger.warning(f"LLM rules not yet implemented: {rule['rule_id']}")
        return {"violation": False}
    
    def _execute_custom_rule_logic(self, rule: Dict[str, Any], user_input: str,
                                  bot_response: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom rule logic"""
        # TODO: Implement custom rule execution
        # This could support Python code execution in a sandbox
        logger.warning(f"Custom rules not yet implemented: {rule['rule_id']}")
        return {"violation": False}
    
    async def execute_all_custom_rules(self, organization_id: str, pillar: str,
                                      user_input: str, bot_response: str) -> List[Dict[str, Any]]:
        """
        Execute all custom rules for a specific pillar
        Returns: List of violations
        """
        # Get custom rules for this pillar
        custom_rules = await self.get_custom_rules(organization_id, pillar)
        
        violations = []
        
        for rule in custom_rules:
            result = self.execute_custom_rule(rule, user_input, bot_response)
            if result.get("violation", False):
                violations.append(result)
        
        logger.debug(f"Executed {len(custom_rules)} custom rules, found {len(violations)} violations")
        
        return violations
    
    def merge_violations(self, default_violations: List[Dict[str, Any]],
                        custom_violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge default and custom rule violations
        """
        all_violations = default_violations + custom_violations
        
        # Sort by severity (CRITICAL > HIGH > MEDIUM > LOW)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_violations.sort(key=lambda v: severity_order.get(v.get("severity", "LOW"), 3))
        
        return all_violations


# Global rule engine instance
rule_engine = RuleEngine()


def get_rule_engine() -> RuleEngine:
    """Get rule engine instance"""
    return rule_engine
