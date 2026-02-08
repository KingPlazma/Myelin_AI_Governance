
from utils import safe_div, normalize

RULE_ID = "FR02"
RULE_NAME = "Disparate Impact Ratio"
CATEGORY = "Group Fairness"
SEVERITY = "High"

PARAMS = {
    "threshold": 0.2,
    "min_samples": 10
}

def evaluate(ctx):
    y_pred = ctx["y_pred"]
    sensitive = ctx["sensitive"]

    g0 = [y_pred[i] for i in range(len(sensitive)) if sensitive[i] == 0]
    g1 = [y_pred[i] for i in range(len(sensitive)) if sensitive[i] == 1]

    if len(g0) < PARAMS["min_samples"] or len(g1) < PARAMS["min_samples"]:
        return {
            "rule_id": RULE_ID,
            "status": "INSUFFICIENT_DATA",
            "normalized_score": 0.0
        }

    r0 = safe_div(sum(g0), len(g0))
    r1 = safe_div(sum(g1), len(g1))

    ratio = safe_div(r0, r1)
    raw = abs(1 - ratio)

    norm = normalize(raw, PARAMS["threshold"])
    status = "PASS" if raw <= PARAMS["threshold"] else "VIOLATION"

    return {
        "rule_id": RULE_ID,
        "name": RULE_NAME,
        "category": CATEGORY,
        "raw_score": round(raw, 4),
        "normalized_score": round(norm, 4),
        "threshold": PARAMS["threshold"],
        "status": status,
        "severity": SEVERITY,
        "explanation": "Deviation from ideal disparate impact",
        "evidence": {
            "ratio": ratio,
            "group0_rate": r0,
            "group1_rate": r1
        }
    }
