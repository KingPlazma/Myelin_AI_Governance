from abc import ABC, abstractmethod

class BiasRule(ABC):
    """
    Execution Standard for all Bias Modules.
    """
    def __init__(self, name: str, description: str, severity: float):
        self.name = name
        self.description = description
        self.severity = severity

    @abstractmethod
    def evaluate(self, user_input: str, bot_response: str) -> dict:
        """
        Logic must return a dictionary with:
        'violation' (bool), 'reason' (str), and 'score' (float).
        """
        pass