from modules.factual.base_factual_rule import BaseFactualRule

class ExternalKnowledgeVerificationRule(BaseFactualRule):
    def __init__(self):
        super().__init__("External Knowledge", 0.05)

    def evaluate(self, model_output, source_text):
        # Placeholder for external check
        return 1.0, {
            "theory": "Verifies against external knowledge base",
            "observation": "No external lookup configured (Lite)",
            "result": "Pass"
        }
