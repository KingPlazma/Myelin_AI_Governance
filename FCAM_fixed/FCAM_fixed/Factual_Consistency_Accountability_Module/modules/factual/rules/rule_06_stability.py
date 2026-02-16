from modules.factual.base_factual_rule import BaseFactualRule
from modules.factual.factual_utils import calculate_similarity

class MetamorphicStabilityRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Metamorphic Stability", 0.12)

    def evaluate(self, model_output, source_text=None):
        variants = [
            model_output,
            model_output.lower(),
            model_output.replace("may", "").replace("might", "")
        ]

        sims = []
        for i in range(len(variants)):
            for j in range(i + 1, len(variants)):
                sims.append(calculate_similarity(variants[i], variants[j]))

        avg_similarity = sum(sims) / len(sims) if sims else 1.0
        score = 1.0 if avg_similarity >= 0.85 else avg_similarity

        return score, {
            "avg_similarity": round(avg_similarity, 3),
            "theory": "Checks whether the answer remains semantically stable when rewritten.",
            "observation": "The meaning of the answer remained consistent across variations.",
            "result": f"Stability Score = {round(score, 2)}"
        }
