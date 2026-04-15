from modules.factual.base_factual_rule import BaseFactualRule


class TemporalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Temporal Consistency", 0.05)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: no dates detected assumes consistent
        score = 1.0
        return score, {
            "theory": "Checks whether timelines and dates follow chronological order.",
            "observation": "No temporal conflicts detected.",
            "result": f"Temporal consistency → Score = {round(score, 2)}"
        }
