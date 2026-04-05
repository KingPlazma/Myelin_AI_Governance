from modules.factual.base_factual_rule import BaseFactualRule

class CausalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Causal Consistency", 0.04)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: check for unsupported because/therefore
        contains_cause = "because" in model_output.lower() or "therefore" in model_output.lower()
        score = 1.0 if not contains_cause else 0.9

        return score, {
            "theory": "Checks whether cause-effect statements are supported.",
            "observation": "No unsupported causal links detected." if score == 1.0 else "Causal reasoning present but unverified.",
            "result": f"Causal consistency → Score = {round(score, 2)}"
        }
