from modules.factual.base_factual_rule import BaseFactualRule
from modules.factual.factual_utils import calculate_similarity

class ClaimLevelVerificationRule(BaseFactualRule):
    def __init__(self):
        # Increased weight from 0.10 to 0.30
        super().__init__("Claim Verification", 0.30)

    def evaluate(self, model_output, source_text):
        claims = [c.strip() for c in model_output.split('.') if c.strip()]
        if not claims:
            return 1.0, {
                "theory": "Checks each atomic factual claim individually.",
                "observation": "No claims found.",
                "result": "Score = 1.0"
            }

        verified = 0
        for c in claims:
            sim = calculate_similarity(c, source_text)
            
            # Stricter Threshold: 0.7
            if sim >= 0.7 or c.lower() in source_text.lower():
                verified += 1
                
        score = verified / len(claims)

        return score, {
            "theory": "Checks factual correctness for each atomic claim.",
            "observation": f"{verified}/{len(claims)} claims match the source.",
            "result": f"Verified claim score = {round(score, 2)}"
        }
