
import importlib, os

class FairnessEnsemble:
    def __init__(self, rules_path):
        self.rules = [
            importlib.import_module(f"rules.{f[:-3]}")
            for f in os.listdir(rules_path)
            if f.endswith(".py") and f != "__init__.py"
        ]

    def run(self, y_true, y_pred, sensitive):
        ctx = {
            "y_true": y_true,
            "y_pred": y_pred,
            "sensitive": sensitive
        }

        results = []
        for r in self.rules:
            out = r.evaluate(ctx)
            if out.get("status") != "INSUFFICIENT_DATA":
                results.append(out)

        if not results:
            return {
                "module": "fairness",
                "overall_score": 0.0,
                "verdict": "INSUFFICIENT_DATA",
                "rules": []
            }

        overall = sum(r["normalized_score"] for r in results) / len(results)

        return {
            "module": "fairness",
            "overall_score": round(overall, 4),
            "verdict": "PASS" if overall < 0.3 else "FAIL",
            "rules": results
        }
