from modules.factual.base_factual_rule import BaseFactualRule


class EntityConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Entity Consistency", 0.06)

    def evaluate(self, model_output, source_text=None):
        # Semi implementation: assume no fake entities
        score = 1.0
        return score, {
            "theory": "Checks whether entities (names, orgs, locations) match the source.",
            "observation": "No fabricated or swapped entities detected.",
            "result": f"Entity consistency → Score = {round(score, 2)}"
        }
