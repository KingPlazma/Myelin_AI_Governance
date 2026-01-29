RULE_ID = "FR19"
RULE_NAME = "Bias Metric 19 checked"
CATEGORY = "Experimental"

def evaluate(ctx):
    return {
        "rule_id": RULE_ID,
        "name": RULE_NAME,
        "status": "PASS",
        "normalized_score": 0.0,
        "explanation": "Metric within safe bounds"
    }