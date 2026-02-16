from modules.factual.base_factual_rule import BaseFactualRule


class CoverageCompletenessRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Coverage Completeness", 0.04)
        self.expected_keys = ["coverage", "duration", "exclusions", "benefits"]

    def evaluate(self, model_output, source_text=None):
        covered = 0
        for k in self.expected_keys:
            if k.lower() in model_output.lower():
                covered += 1

        score = covered / len(self.expected_keys)

        return score, {
            "theory": "Checks whether essential aspects are included.",
            "observation": f"{covered}/{len(self.expected_keys)} required aspects covered.",
            "result": f"Coverage completeness score = {round(score, 2)}"
        }
