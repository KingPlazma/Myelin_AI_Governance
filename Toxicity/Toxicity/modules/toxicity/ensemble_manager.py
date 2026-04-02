from datetime import datetime
import os
import importlib
import inspect
import logging
from typing import List

from modules.toxicity.base_toxicity_rule import BaseToxicityRule

logger = logging.getLogger("EnsembleManager")

class ToxicityEnsembleManager:
    """
    Runs all toxicity rules in parallel (logical ensemble)
    Aggregates violations into a single governance decision
    """

    def __init__(self):
        self.rules: List[BaseToxicityRule] = []
        self._load_rules()

    def _load_rules(self):
        """
        Dynamically loads all BaseToxicityRule subclasses 
        from the rules directory.
        """
        rules_path = os.path.join(os.path.dirname(__file__), "rules")
        
        if not os.path.exists(rules_path):
            logger.error(f"Rules directory not found at {rules_path}")
            return

        for filename in os.listdir(rules_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"modules.toxicity.rules.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseToxicityRule) and 
                            obj is not BaseToxicityRule):
                            self.rules.append(obj())
                            logger.info(f"Successfully registered: {name}")
                except Exception as e:
                    logger.error(f"Failed to load rule from {filename}: {e}")

        # Verification
        expected_rules = 20
        if len(self.rules) < expected_rules:
            logger.warning(f"CRITICAL: Only {len(self.rules)} rules loaded. Expected {expected_rules}.")
        else:
            logger.info("Full suite of 20 rules verified and active.")

    def run_full_audit(self, user_input: str, bot_response: str) -> dict:
        """Executes all loaded rules and aggregates scores."""
        violations = []
        total_score = 0.0
        categories = set()
        reports = []

        for rule in self.rules:
            try:
                result = rule.evaluate(user_input, bot_response)
                
                # Standardize report for detail view
                reports.append({
                    "rule_name": rule.name,
                    "violation": result.get("violation", False),
                    "reason": result.get("reason", "N/A"),
                    "score": result.get("score", result.get("weight", 0.0)) # Fallback to weight if score missing
                })

                if result.get("violation"):
                    # Legacy Violation Structure (for backward compatibility if needed, but prioritizing new structure)
                    # Inject metadata if missing
                    result["rule_id"] = rule.rule_id
                    result["rule_name"] = rule.name
                    result["category"] = rule.category
                    result["severity"] = getattr(rule, "severity", "HIGH")
                    
                    violations.append(result)
                    total_score += result.get("weight", 0.0)
                    categories.add(rule.category)
            except Exception as e:
                logger.error(f"Rule execution failed: {e}")
                reports.append({
                    "rule_name": rule.name,
                    "violation": False,
                    "reason": f"Error: {str(e)}",
                    "score": 0.0
                })

        # Decision Logic (Keep existing business logic)
        if total_score >= 1.5:
            decision = "BLOCK"
            risk = "CRITICAL"
        elif total_score >= 0.7:
            decision = "WARN"
            risk = "HIGH"
        elif total_score > 0:
            decision = "ALLOW_WITH_CAUTION"
            risk = "MEDIUM"
        else:
            decision = "ALLOW"
            risk = "LOW"

        return {
            "module": "toxicity",
            "timestamp": datetime.utcnow().isoformat(),
            "toxicity_score": round(total_score, 2),
            "risk_level": risk,
            "decision": decision,
            "violated_categories": list(categories),
            "violations": violations,
            "details": reports # Added to match bias/fairness structure
        }

    # Alias for backward compatibility during transitions, or update callers
    def evaluate(self, user_input: str, bot_response: str) -> dict:
        return self.run_full_audit(user_input, bot_response)
