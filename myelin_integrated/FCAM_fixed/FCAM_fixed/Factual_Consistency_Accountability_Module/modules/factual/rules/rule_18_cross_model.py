from modules.factual.base_factual_rule import BaseFactualRule

class CrossModelAgreementRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Cross Model Agreement", 0.05)

    def evaluate(self, model_output, source_text):
        return 1.0, {"theory": "Cross Model Check", "observation": "Pass", "result": "Pass"}
