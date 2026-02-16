from modules.factual.base_factual_rule import BaseFactualRule


class DomainSensitivityRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Domain Sensitivity", 0.08)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: assume domain is non-critical
        domain = "Insurance"
        score = 1.0

        return score, {
            "theory": "Applies stricter rules for safety-critical domains such as medical, legal, or finance.",
            "observation": f"Domain identified as: {domain}",
            "result": f"Domain sensitivity → Score = {round(score, 2)}"
        }
