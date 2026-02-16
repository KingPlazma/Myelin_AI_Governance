from modules.factual.base_factual_rule import BaseFactualRule


class InternalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Internal Logical Consistency", 0.06)

    def evaluate(self, model_output, source_text=None):
        # Simple deterministic contradiction check
        contradictions = [
            ("before", "after"),
            ("increase", "decrease"),
            ("yes", "no"),
            ("true", "false")
        ]

        text = model_output.lower()
        found = any(a in text and b in text for a, b in contradictions)

        score = 0.0 if found else 1.0
        return score, {
    "contradiction_detected": found,
    "theory": "Checks whether the answer contradicts itself internally.",
    "observation": "No conflicting statements were found in the output."
        if not found else "Contradictory statements were detected.",
    "result": f"Logically consistent → Score = {round(score, 2)}"
}

