from modules.toxicity.base_toxicity_rule import BaseToxicityRule
from modules.toxicity.services.ollama_service import OllamaService

class RuleAIJudgement(BaseToxicityRule):
    def __init__(self):
        super().__init__("TOX-19", "AI Contextual Analysis", "AI Safety", 1.0)
        self.service = OllamaService()

    def evaluate(self, user_input, bot_response):
        try:
            analysis = self.service.analyze_toxicity(user_input, bot_response)
            
            if analysis.get("violation"):
                return {
                    "violation": True,
                    "rule_id": self.rule_id,
                    "rule_name": self.name,
                    "category": self.category,
                    "severity": analysis.get("severity", "MEDIUM").upper(),
                    "confidence": analysis.get("confidence", 0.5),
                    "trigger_span": "AI_DETECTED",
                    "reason": analysis.get("reason", "AI detected contextual violation"),
                    "weight": self.weight
                }
        except Exception:
            pass
            
        return {"violation": False}
