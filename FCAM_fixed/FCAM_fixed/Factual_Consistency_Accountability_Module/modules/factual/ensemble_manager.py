class FactualEnsembleManager:
    def __init__(self, rules):
        self.rules = rules

    def evaluate(self, model_output, source_text=None):
        final_score = 0.0
        report = {}

        for rule in self.rules:
            score, details = rule.evaluate(model_output, source_text)
            weighted_score = score * rule.weight
            final_score += weighted_score

            report[rule.name] = {
                "score": score,
                "weight": rule.weight,
                "details": details
            }

        return final_score, report
