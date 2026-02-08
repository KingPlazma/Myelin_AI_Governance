from modules.factual.base_factual_rule import BaseFactualRule
import re

class NumericalConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Numerical Consistency", 0.10)

    def evaluate(self, model_output, source_text):
        if not source_text: return 1.0, {}
        
        # Extract numbers
        out_nums = set(re.findall(r'\d+', model_output))
        src_nums = set(re.findall(r'\d+', source_text))
        
        # Check if numbers in output exist in source
        if not out_nums: return 1.0, {}
        
        valid = [n for n in out_nums if n in src_nums]
        score = len(valid) / len(out_nums)
        
        return score, {
            "theory": "Verifies numbers appear in source",
            "observation": f"{len(valid)}/{len(out_nums)} numbers verified",
            "result": f"Score: {score:.2f}"
        }
