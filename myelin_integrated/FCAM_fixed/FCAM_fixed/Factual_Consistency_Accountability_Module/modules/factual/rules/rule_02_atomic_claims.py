from modules.factual.base_factual_rule import BaseFactualRule

class AtomicClaimDecompositionRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Atomic Claim Decomposition", 0.05)

    def evaluate(self, model_output, source_text):
        # Split by sentence delimiters
        claims = [s.strip() for s in model_output.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        count = len(claims)
        
        return 1.0, {
            "theory": "Decomposes output into atomic claims",
            "observation": f"Decomposed into {count} claims",
            "result": "Pass"
        }
