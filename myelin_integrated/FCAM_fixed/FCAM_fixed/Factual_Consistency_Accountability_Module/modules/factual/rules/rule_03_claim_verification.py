from modules.factual.base_factual_rule import BaseFactualRule

class ClaimLevelVerificationRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Claim Verification", 0.10)

    def evaluate(self, model_output, source_text):
        if not source_text: return 1.0, {}
        
        # Check if key phrases from output exist in source
        claims = [s.strip() for s in model_output.split('.') if len(s) > 10]
        verified = 0
        for claim in claims:
            # Check if 50% of words in claim appear in source
            claim_words = set(claim.lower().split())
            src_words = set(source_text.lower().split())
            overlap = len(claim_words.intersection(src_words))
            if len(claim_words) > 0 and (overlap / len(claim_words)) > 0.5:
                verified += 1
                
        score = verified / len(claims) if claims else 1.0
        return score, {
            "theory": "Verifies claims against source keywords",
            "observation": f"{verified}/{len(claims)} claims verified",
            "result": f"Score: {score:.2f}"
        }
