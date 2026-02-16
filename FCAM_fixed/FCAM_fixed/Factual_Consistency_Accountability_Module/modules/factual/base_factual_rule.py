from abc import ABC, abstractmethod

class BaseFactualRule(ABC):
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

    @abstractmethod
    def evaluate(self, model_output, source_text=None):
        pass
