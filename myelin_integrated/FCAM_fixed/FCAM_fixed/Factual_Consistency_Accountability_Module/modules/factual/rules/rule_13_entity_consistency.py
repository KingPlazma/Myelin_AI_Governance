from modules.factual.base_factual_rule import BaseFactualRule
import re

class EntityConsistencyRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Entity Consistency", 0.05)

    def evaluate(self, model_output, source_text):
        if not source_text: return 1.0, {}
        
        # Find capitalized words (Entities)
        out_ents = set(re.findall(r'[A-Z][a-z]+', model_output))
        src_ents = set(re.findall(r'[A-Z][a-z]+', source_text))
        
        if not out_ents: return 1.0, {}
        
        valid = [e for e in out_ents if e in src_ents]
        score = len(valid) / len(out_ents)
        
        # Boost score for leniency
        score = min(1.0, score + 0.2)
        
        return score, {
            "theory": "Verifies entities (Names/Places) appear in source",
            "observation": f"{len(valid)}/{len(out_ents)} entities verified",
            "result": f"Score: {score:.2f}"
        }
