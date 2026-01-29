from modules.factual.base_factual_rule import BaseFactualRule

class MetamorphicStabilityRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Metamorphic Stability", 0.05)

    def evaluate(self, model_output, source_text):
        # Check for repeated phrases (hallucination loop)
        words = model_output.lower().split()
        unique = len(set(words))
        total = len(words)
        
        ratio = unique / total if total > 0 else 1.0
        score = 1.0 if ratio > 0.5 else 0.5 # Penalize if >50% words are repetitions
        
        return score, {
            "theory": "Checks for repetition loops",
            "observation": f"Unique word ratio: {ratio:.2f}",
            "result": f"Score: {score:.2f}"
        }
