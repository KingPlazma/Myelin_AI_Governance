from modules.factual.base_factual_rule import BaseFactualRule


UNCERTAINTY_WORDS = [
    "may", "might", "possibly",
    "likely", "uncertain", "approximately"
]

class UncertaintySignalingRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Uncertainty Signaling", 0.03)

    def evaluate(self, model_output, source_text=None):
        present = any(word in model_output.lower() for word in UNCERTAINTY_WORDS)
        score = 1.0 if present else 0.5
        return score, {
    "uncertainty_present": present,
    "theory": "Checks whether uncertainty is expressed for weakly supported claims.",
    "observation": "Proper uncertainty markers were used."
        if present else "Uncertainty markers are missing.",
    "result": f"Proper uncertainty signaling → Score = {round(score, 2)}"
}

