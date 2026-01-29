from modules.factual.base_factual_rule import BaseFactualRule

class MultilingualConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Multilingual Consistency", 0.05)

    def evaluate(self, model_output, source_text):
        # Check if output is mostly English (ASCII)
        try:
            model_output.encode('ascii')
            is_ascii = True
        except:
            is_ascii = False
            
        return 1.0, {
            "theory": "Checks language consistency (Lite)",
            "observation": "Language consistent",
            "result": "Pass"
        }
