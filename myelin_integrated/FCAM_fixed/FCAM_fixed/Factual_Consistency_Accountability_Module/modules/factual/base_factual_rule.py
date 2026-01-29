class BaseFactualRule:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

    def evaluate(self, model_output, source_text):
        """
        Evaluate the rule.
        Returns: (score, details_dict)
        """
        raise NotImplementedError("Subclasses must implement evaluate")
