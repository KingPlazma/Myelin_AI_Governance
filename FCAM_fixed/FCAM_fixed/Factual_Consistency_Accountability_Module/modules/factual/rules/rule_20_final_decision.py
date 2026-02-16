from modules.factual.base_factual_rule import BaseFactualRule


class FinalFactualConfidenceRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Final Decision", 0.0)  # meta rule

    def evaluate(self, model_output, source_text=None, final_score=None):
        if final_score is None:
            return 1.0, {
                "theory": "Aggregates weighted scores to determine pass/warn/reject.",
                "observation": "Final score not provided.",
                "result": "Cannot determine decision."
            }

        if final_score >= 0.85:
            verdict = "PASS"
        elif 0.65 <= final_score < 0.85:
            verdict = "WARN"
        else:
            verdict = "REJECT"

        return 1.0, {
            "theory": "Applies final confidence thresholding over combined rule outputs.",
            "observation": f"Final factual score = {round(final_score, 3)}",
            "result": f"Decision: {verdict}"
        }
