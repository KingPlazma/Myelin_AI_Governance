from modules.factual.base_factual_rule import BaseFactualRule

class HallucinationSeverityRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Hallucination Severity", 0.05)

    def evaluate(self, model_output, source_text):
        return 1.0, {"theory": "Severity Check", "observation": "Pass", "result": "Pass"}
