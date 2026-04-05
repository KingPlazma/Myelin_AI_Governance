
from utils import confusion, normalize, safe_div

RULE_ID = "FR15"
RULE_NAME = "Treatment Equality"
CATEGORY = "Advanced Fairness"
SEVERITY = "Medium"

PARAMS = {
    "threshold": 0.2,
    "min_samples": 5
}

def evaluate(ctx):
    y_true = ctx["y_true"]
    y_pred = ctx["y_pred"]
    sensitive = ctx["sensitive"]

    # Split data by group
    g0_indices = [i for i in range(len(sensitive)) if sensitive[i] == 0]
    g1_indices = [i for i in range(len(sensitive)) if sensitive[i] == 1]

    if len(g0_indices) < PARAMS["min_samples"] or len(g1_indices) < PARAMS["min_samples"]:
        return {
            "rule_id": RULE_ID,
            "status": "INSUFFICIENT_DATA",
            "normalized_score": 0.0
        }

    # Helper to get metrics for a group
    def get_metrics(indices):
        y_t = [y_true[i] for i in indices]
        y_p = [y_pred[i] for i in indices]
        tp, tn, fp, fn = confusion(y_t, y_p)
        total = len(indices)
        
        # Fundamental stats
        tpr = safe_div(tp, tp + fn)
        fpr = safe_div(fp, fp + tn)
        tnr = safe_div(tn, tn + fp)
        fnr = safe_div(fn, fn + tp)
        ppv = safe_div(tp, tp + fp) # Precision
        npv = safe_div(tn, tn + fn)
        fdr = safe_div(fp, fp + tp)
        for_ = safe_div(fn, fn + tn)
        acc = safe_div(tp + tn, total)
        f1 = safe_div(2 * tp, 2 * tp + fp + fn)
        
        return locals()

    m0 = get_metrics(g0_indices)
    m1 = get_metrics(g1_indices)

    # Metric Calculation Logic
    r0 = safe_div(m0['fn'], m0['fp']); r1 = safe_div(m1['fn'], m1['fp']); raw = abs(r0 - r1)
    val0 = safe_div(m0['fn'], m0['fp']); val1 = safe_div(m1['fn'], m1['fp'])
    explanation = f'Ratio of False Negatives to False Positives'

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
        "explanation": explanation,
        "evidence": {
            "group0": round(val0, 4),
            "group1": round(val1, 4)
        }
    }
