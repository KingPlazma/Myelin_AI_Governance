import os
import importlib
import inspect
import logging
from typing import List
from modules.bias.base_bias_rule import BiasRule

logger = logging.getLogger("EnsembleManager")

class BiasEnsembleManager:
    def __init__(self):
        self.rules: List[BiasRule] = []
        self._load_rules()

    def _load_rules(self):
        """
        Execution Level: Dynamically loads all BiasRule subclasses 
        from the rules directory.
        """
        rules_path = os.path.join(os.path.dirname(__file__), "rules")
        
        # Verify the path exists
        if not os.path.exists(rules_path):
            logger.error(f"Rules directory not found at {rules_path}")
            return

        # Iterate through every file in the rules folder
        for filename in os.listdir(rules_path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"modules.bias.rules.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    
                    # Find classes that are subclasses of BiasRule
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BiasRule) and 
                            obj is not BiasRule):
                            self.rules.append(obj())
                            logger.info(f"Successfully registered: {name}")
                except Exception as e:
                    logger.error(f"Failed to load rule from {filename}: {e}")

        # DIAGNOSTIC CHECK: The "Missing Rule" Alert
        if len(self.rules) < 20:
            logger.warning(f"CRITICAL: Only {len(self.rules)} rules loaded. Expected 20.")
            self._debug_missing_rules(rules_path)
        else:
            logger.info("Full suite of 20 rules verified and active.")

    def _debug_missing_rules(self, path):
        """Prints the files that failed to register a class."""
        files = [f for f in os.listdir(path) if f.endswith(".py") and f != "__init__.py"]
        logger.info(f"Files found in directory: {len(files)}")
        if len(files) > len(self.rules):
            logger.info("Check if class names inside files correctly inherit from BiasRule.")

    def run_full_audit(self, user_input: str, bot_response: str):
        """Executes all loaded rules and aggregates scores."""
        reports = []
        cumulative_score = 0.0
        
        for rule in self.rules:
            result = rule.evaluate(user_input, bot_response)
            reports.append({
                "rule_name": rule.name,
                "violation": result.get("violation", False),
                "reason": result.get("reason", "N/A"),
                "score": result.get("score", 0.0)
            })
            cumulative_score += result.get("score", 0.0)

        # Normalize score
        gbi = min(1.0, cumulative_score / 2.0)
        
        return {
            "global_bias_index": round(gbi, 3),
            "total_rules_executed": len(self.rules),
            "details": reports
        }