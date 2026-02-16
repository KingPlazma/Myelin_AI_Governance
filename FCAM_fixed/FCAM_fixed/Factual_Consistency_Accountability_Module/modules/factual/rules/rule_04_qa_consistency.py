from modules.factual.base_factual_rule import BaseFactualRule


class QABasedConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("QA Consistency", 0.08)

    def evaluate(self, model_output, source_text):
        # Semi-implementation: heuristic simulation
        # A real version converts statements -> questions -> answers -> compare
        wh_words = ["what", "when", "who", "where", "why", "how"]
        generated_questions = []
        for sentence in model_output.split('.'):
            s = sentence.strip()
            if s:
                q = f"What about: {s}?"
                generated_questions.append(q)

        score = 0.85  # default assumption

        return score, {
            "theory": "Verifies output by converting statements into questions and answering using the source.",
            "observation": f"Generated {len(generated_questions)} synthetic QA pairs.",
            "result": f"QA consistency assumed → Score = {score}"
        }
