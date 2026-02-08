from modules.factual.base_factual_rule import BaseFactualRule
import re

class TemporalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Temporal Consistency", 0.05)

    def evaluate(self, model_output, source_text):
        # Find years (19xx, 20xx)
        years = re.findall(r'(19|20)\d{2}', model_output)
        return 1.0, {"theory": "Temporal Check", "observation": f"Found {len(years)} dates", "result": "Pass"}
