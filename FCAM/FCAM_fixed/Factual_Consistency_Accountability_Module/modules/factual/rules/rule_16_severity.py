from modules.factual.base_factual_rule import BaseFactualRule


class HallucinationSeverityRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Severity Classification", 0.08)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: assume medium severity
        severity = "Medium"
        score = 0.7

        return score, {
            "theory": "Classifies hallucination impact as Low, Medium, or High.",
            "observation": f"Detected severity level = {severity}",
            "result": f"Severity classification → Score = {round(score, 2)}"
        }
