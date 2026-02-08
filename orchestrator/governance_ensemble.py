import os
import importlib
import inspect
import logging
from typing import List
from modules.governance.base_governance_rule import GovernanceRule

logger = logging.getLogger("GovEnsembleManager")

class GovernanceEnsembleManager:
    def __init__(self):
        self.rules: List[GovernanceRule] = []
        self._load_rules()

    def _load_rules(self):
        # Pointing to the new 'governance/rules' directory
        rules_path = os.path.join(os.path.dirname(__file__), "rules")
        
        if not os.path.exists(rules_path):
            logger.error(f"Rules directory not found at {rules_path}")
            return

        for filename in os.listdir(rules_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"modules.governance.rules.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, GovernanceRule) and 
                            obj is not GovernanceRule):
                            # Prevent duplicates
                            if obj not in [type(r) for r in self.rules]:
                                self.rules.append(obj())
                                logger.info(f"✅ Registered Gov Rule: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error loading {filename}: {e}")

    def run_full_audit(self, user_input: str, bot_response: str):
        reports = []
        cumulative_score = 0.0
        
        for rule in self.rules:
            result = rule.evaluate(user_input, bot_response)
            reports.append({
                "rule_name": rule.name,
                "violation": result.get("violation", False),
                "reason": result.get("reason", "N/A"),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            })
            cumulative_score += result.get("score", 0.0)

        return {
            "governance_risk_score": min(1.0, cumulative_score / 2.0),
            "details": reports
        }