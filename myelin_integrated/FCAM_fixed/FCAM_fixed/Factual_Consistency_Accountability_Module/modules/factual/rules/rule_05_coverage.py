from modules.factual.base_factual_rule import BaseFactualRule

class CoverageCompletenessRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Coverage Completeness", 0.05)

    def evaluate(self, model_output, source_text):
        if not source_text: return 1.0, {}
        
        ratio = len(model_output) / len(source_text)
        score = min(1.0, ratio * 1.5) # Expect summary to be at least 66% of source length
        
        return score, {
            "theory": "Checks if output covers sufficient source content",
            "observation": f"Length ratio: {ratio:.2f}",
            "result": f"Score: {score:.2f}"
        }
