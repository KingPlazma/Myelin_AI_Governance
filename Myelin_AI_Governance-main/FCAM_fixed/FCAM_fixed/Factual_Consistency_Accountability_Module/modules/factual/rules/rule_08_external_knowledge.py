from modules.factual.base_factual_rule import BaseFactualRule


class ExternalKnowledgeVerificationRule(BaseFactualRule):
    def __init__(self):
        super().__init__("External Knowledge Verification", 0.06)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: no real retrieval, assume neutral
        contradictions = 0
        score = 1.0 if contradictions == 0 else 0.5

        return score, {
            "theory": "Validates claims against trusted external sources.",
            "observation": "No external contradictions detected (simulated).",
            "result": f"External verification → Score = {round(score, 2)}"
        }
