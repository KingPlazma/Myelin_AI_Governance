from modules.factual.base_factual_rule import BaseFactualRule


class AtomicClaimDecompositionRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Atomic Claim Decomposition", 0.05)

    def evaluate(self, model_output, source_text=None):
        delimiters = [" and ", " or ", " because ", " which ", " who "]
        claims = [model_output]

        for d in delimiters:
            temp = []
            for c in claims:
                temp.extend(c.split(d))
            claims = temp

        claims = [c.strip().rstrip('.') for c in claims if c.strip()]

        score = 1.0

        return score, {
            "theory": "Splits long sentences into atomic factual claims.",
            "observation": f"Extracted {len(claims)} factual claims.",
            "result": f"Decomposition successful → Score = 1.0",
            "claims": claims
        }
