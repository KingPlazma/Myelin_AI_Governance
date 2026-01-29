from modules.factual.base_factual_rule import BaseFactualRule

class TokenCorrectionRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Token Correction", 0.05)

    def evaluate(self, model_output, source_text):
        return 1.0, {"theory": "Token Correction", "observation": "Pass", "result": "Pass"}
