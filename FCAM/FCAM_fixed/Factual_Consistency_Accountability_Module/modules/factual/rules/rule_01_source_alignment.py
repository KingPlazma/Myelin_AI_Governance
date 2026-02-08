from modules.factual.base_factual_rule import BaseFactualRule
from modules.factual.factual_utils import calculate_similarity

class SourceAlignmentRule(BaseFactualRule):
    def __init__(self):
        # Increased weight from 0.10 to 0.40 because this is the Core Fact Check
        super().__init__("Source Alignment", 0.40)

    def evaluate(self, model_output, source_text):
        if not source_text:
            return 1.0, {
                "theory": "Checks whether each factual sentence is grounded in the source text.",
                "observation": "No source text provided; defaulting to aligned.",
                "result": "Score = 1.0 (no source provided)"
            }

        sentences = [s.strip() for s in model_output.split('.') if s.strip()]
        aligned = 0
        
        for s in sentences:
            sim = calculate_similarity(s, source_text)
            
            # Stricter Threshold: 0.7 
            # With Jaccard (The sky is green vs blue) -> 0.6 -> Fails -> Good!
            if sim >= 0.7: 
                aligned += 1
            else:
                # Substring fallback
                if s.lower() in source_text.lower():
                    aligned += 1

        score = aligned / len(sentences) if sentences else 1.0

        return score, {
            "theory": "Ensures every factual sentence matches evidence from the source document.",
            "observation": f"{aligned}/{len(sentences)} sentences aligned with source.",
            "result": f"Alignment score = {round(score, 2)} → Score = {round(score, 2)}"
        }
