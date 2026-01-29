from modules.factual.base_factual_rule import BaseFactualRule

class TokenValidationRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Token Validation", 0.05)

    def evaluate(self, model_output, source_text):
        # Check for 'UNK' or '<|endoftext|>' artifacts
        artifacts = ["<unk>", "UNK", "[UNK]", "<|endoftext|>"]
        found = [a for a in artifacts if a in model_output]
        
        score = 0.0 if found else 1.0
        return score, {
            "theory": "Checks for generation artifacts",
            "observation": f"Artifacts found: {found}",
            "result": f"Score: {score:.2f}"
        }
