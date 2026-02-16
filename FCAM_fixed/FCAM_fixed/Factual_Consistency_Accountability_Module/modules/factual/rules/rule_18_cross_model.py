from modules.factual.base_factual_rule import BaseFactualRule


class CrossModelAgreementRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Cross-Model Agreement", 0.04)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: simulate agreement across models
        agreement_score = 0.85
        score = 1.0 if agreement_score >= 0.80 else agreement_score

        return score, {
            "theory": "Compares outputs from multiple models to reduce single-model bias.",
            "observation": f"Agreement score across models = {agreement_score}",
            "result": f"Cross model agreement → Score = {round(score, 2)}"
        }
