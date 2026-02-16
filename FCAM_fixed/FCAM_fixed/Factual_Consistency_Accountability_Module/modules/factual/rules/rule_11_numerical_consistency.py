import re
from modules.factual.base_factual_rule import BaseFactualRule

class NumericalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Numerical Consistency", 0.07)

    def evaluate(self, model_output, source_text=None):
        if not source_text:
            return 1.0, {"reason": "no source"}

        output_nums = re.findall(r'\d+', model_output)
        source_nums = re.findall(r'\d+', source_text)

        mismatch = [n for n in output_nums if n not in source_nums]
        score = 1.0 if not mismatch else 0.0

        return score, {
    "numerical_mismatch": mismatch,
    "theory": "Ensures numerical values exactly match the source.",
    "observation": f"Numerical mismatch detected: {mismatch}"
        if mismatch else "All numerical values match the source.",
    "result": f"High-risk numerical hallucination → Score = {round(score, 2)}"
}

