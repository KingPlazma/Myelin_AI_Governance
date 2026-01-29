from modules.factual.base_factual_rule import BaseFactualRule

class SourceAlignmentRule(BaseFactualRule):
    def __init__(self):
        super().__init__("Source Alignment", 0.10)

    def evaluate(self, model_output, source_text):
        if not source_text:
            return 1.0, {"theory": "Source Alignment", "observation": "No source provided", "result": "Pass"}
        
        # Simple Jaccard Similarity
        out_words = set(model_output.lower().split())
        src_words = set(source_text.lower().split())
        
        if not out_words: return 1.0, {}
        
        intersection = len(out_words.intersection(src_words))
        union = len(out_words.union(src_words))
        score = intersection / union if union > 0 else 0.0
        
        # Boost score for 'Lite' version to be lenient
        final_score = min(1.0, score * 2.5) 
        
        return final_score, {
            "theory": "Checks word overlap with source (Lite Mode)",
            "observation": f"Word overlap: {intersection}/{len(out_words)} unique words",
            "result": f"Score: {final_score:.2f}"
        }
