from abc import ABC, abstractmethod

class BaseToxicityRule(ABC):
    def __init__(self, rule_id: str, name: str, category: str, weight: float):
        self.rule_id = rule_id
        self.name = name
        self.category = category
        self.weight = weight

    @abstractmethod
    def evaluate(self, user_input: str, bot_response: str) -> dict:
        """
        Returns:
        {
            "violation": bool,
            "reason": str,
            "score": float
        }
        """
        pass
