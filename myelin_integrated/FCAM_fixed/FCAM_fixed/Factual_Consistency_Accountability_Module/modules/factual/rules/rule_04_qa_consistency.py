from modules.factual.base_factual_rule import BaseFactualRule

class QABasedConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("QA Consistency", 0.05)

    def evaluate(self, model_output, source_text):
        # Lite version: Checks for contradictions (not, never, no)
        negations = ["not", "never", "no ", "n't", "false"]
        count = sum(1 for n in negations if n in model_output.lower())
        
        score = 1.0 if count < 3 else 0.8 # Penalize heavy negation usage as potential confusion
        return score, {
            "theory": "Checks for internal contradictions (Lite)",
            "observation": f"Found {count} negations",
            "result": f"Score: {score:.2f}"
        }
