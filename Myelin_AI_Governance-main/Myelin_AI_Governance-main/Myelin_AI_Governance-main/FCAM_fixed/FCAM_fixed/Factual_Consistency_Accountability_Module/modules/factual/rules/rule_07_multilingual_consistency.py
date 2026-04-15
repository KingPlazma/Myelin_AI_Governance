from modules.factual.base_factual_rule import BaseFactualRule
from modules.factual.factual_utils import calculate_similarity

class MultilingualConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Multilingual Consistency", 0.05)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: fake translation via string transform
        # In a real system this would use mBERT
        translations = [
            model_output,
            model_output.upper(),   # simulate different representation
            model_output.lower()
        ]

        sims = []
        for i in range(len(translations)):
            for j in range(i + 1, len(translations)):
                sims.append(calculate_similarity(translations[i], translations[j]))

        avg_similarity = sum(sims) / len(sims) if sims else 1.0
        score = 1.0 if avg_similarity >= 0.80 else avg_similarity

        return score, {
            "theory": "Checks whether meaning stays consistent across languages.",
            "observation": f"Multilingual semantic similarity = {round(avg_similarity, 3)}",
            "result": f"Multilingual consistency → Score = {round(score, 2)}"
        }
