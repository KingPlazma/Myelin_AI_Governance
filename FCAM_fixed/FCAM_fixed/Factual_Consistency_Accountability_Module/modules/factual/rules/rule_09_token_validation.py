import re
from modules.factual.base_factual_rule import BaseFactualRule


class TokenValidationRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Token-Level Fact Validation", 0.08)

    def evaluate(self, model_output, source_text=None):
        if not source_text:
            return 1.0, {"reason": "no source"}

        tokens = re.findall(r'\₹?\d+', model_output)
        mismatches = [t for t in tokens if t not in source_text]

        score = 1.0 if not mismatches else max(0, 1 - 0.2 * len(mismatches))
        return score, {
    "mismatched_tokens": mismatches,
    "theory": "Validates fine-grained factual tokens such as numbers and dates.",
    "observation": f"Token mismatch detected: {mismatches}"
        if mismatches else "All factual tokens match the source.",
    "result": f"Minor factual mismatch detected → Score = {round(score, 2)}"
}

