from modules.factual.base_factual_rule import BaseFactualRule

class DomainSensitivityRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Domain Sensitivity", 0.05)

    def evaluate(self, model_output, source_text):
        return 1.0, {"theory": "Domain Check", "observation": "Pass", "result": "Pass"}
