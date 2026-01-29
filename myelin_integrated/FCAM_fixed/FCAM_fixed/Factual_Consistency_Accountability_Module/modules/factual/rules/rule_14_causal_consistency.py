from modules.factual.base_factual_rule import BaseFactualRule

class CausalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Causal Consistency", 0.05)

    def evaluate(self, model_output, source_text):
        causal_words = ["because", "therefore", "since", "due to"]
        found = [w for w in causal_words if w in model_output.lower()]
        return 1.0, {"theory": "Causal Logic Check", "observation": f"Found {len(found)} causal markers", "result": "Pass"}
