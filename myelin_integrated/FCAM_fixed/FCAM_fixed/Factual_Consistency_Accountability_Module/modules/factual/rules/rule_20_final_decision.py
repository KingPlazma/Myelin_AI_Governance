from modules.factual.base_factual_rule import BaseFactualRule

class FinalFactualConfidenceRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Final Confidence Score", 0.0)

    def evaluate(self, model_output, source_text):
        return 1.0, {"theory": "Final Aggregation", "observation": "Pass", "result": "Pass"}
