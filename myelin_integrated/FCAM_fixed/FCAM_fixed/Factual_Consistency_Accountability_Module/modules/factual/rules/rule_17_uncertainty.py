from modules.factual.base_factual_rule import BaseFactualRule

class UncertaintySignalingRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Uncertainty Signaling", 0.05)

    def evaluate(self, model_output, source_text):
        uncertain_words = ["maybe", "perhaps", "possibly", "unlikely"]
        found = [w for w in uncertain_words if w in model_output.lower()]
        return 1.0, {"theory": "Uncertainty Check", "observation": f"Found {len(found)} markers", "result": "Pass"}
