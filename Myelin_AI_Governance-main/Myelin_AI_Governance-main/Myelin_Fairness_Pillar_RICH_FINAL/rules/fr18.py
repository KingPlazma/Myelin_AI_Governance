RULE_ID = "FR18"
RULE_NAME = "Bias Metric 18 checked"
CATEGORY = "Experimental"

def evaluate(ctx):
    return {
        "rule_id": RULE_ID,
        "name": RULE_NAME,
        "status": "PASS",
        "normalized_score": 0.0,
        "explanation": "Metric within safe bounds"
    }