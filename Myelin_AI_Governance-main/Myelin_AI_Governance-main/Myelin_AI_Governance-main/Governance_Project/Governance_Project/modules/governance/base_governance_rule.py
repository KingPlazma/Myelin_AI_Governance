from abc import ABC, abstractmethod

class GovernanceRule(ABC):
    """
    GOVERNANCE AUDIT SYSTEM: Base Rule Architecture.
    Every governance rule (Privacy, GDPR, Compliance) must inherit from this.
    """
    def __init__(self, name: str, description: str, severity: float):
        self.name = name
        self.description = description
        self.severity = severity

    @abstractmethod
    def evaluate(self, user_input: str, bot_response: str) -> dict:
        """
        Must return: {
            "violation": bool,
            "reason": str,
            "score": float,
            "metadata": dict (optional)
        }
        """
        pass