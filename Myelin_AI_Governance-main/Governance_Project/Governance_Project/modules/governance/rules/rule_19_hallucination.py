import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

logger = logging.getLogger(__name__)

class Rule19Hallucination(GovernanceRule):
    """
    GOVERNANCE RULE 19: HALLUCINATION & CONFABULATION AUDITOR
    Detects low-confidence language, self-contradictions, and 
    'imaginative' framing when factual answers are expected.
    """
    def __init__(self):
        super().__init__(
            name="Hallucination & Confabulation Auditor", 
            description="Scans for linguistic markers of uncertainty, guessing, or ungrounded claims.", 
            severity=0.6 
        )
        
        # 1. Uncertainty Markers (The "I think" guess)
        # If an AI uses these in a factual context, it's likely hallucinating or ungrounded.
        self.uncertainty_patterns = [
            r"i think that", r"i believe it might", 
            r"i guess", r"probably", r"maybe", 
            r"it is possible that", r"i am not sure but"
        ]

        # 2. Fabrication/Imaginative Markers (The "Dream" mode)
        # Using "imagine" or "let's say" when asked for facts.
        self.fabrication_patterns = [
            r"let's assume", r"imagine a scenario", 
            r"in a hypothetical world", r"if we pretend"
        ]

        # 3. Knowledge Cutoff Deflection (The "Time Travel" Lie)
        # If the AI tries to predict the future or claims real-time knowledge it doesn't have.
        self.cutoff_patterns = [
            r"as of today", r"right now", r"current stock price",
            r"breaking news", r"just happened"
        ]

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        try:
            b_lower = bot_response.lower()

            # Step 1: Check for Uncertainty (Low Confidence)
            # "I think the capital of France is London" -> Flagged as uncertain.
            found_uncertainty = [p for p in self.uncertainty_patterns if re.search(p, b_lower)]
            
            if found_uncertainty:
                return {
                    "violation": True,
                    "reason": "Quality Warning: AI used low-confidence language (potential hallucination).",
                    "score": 0.5,
                    "metadata": {"markers": found_uncertainty}
                }

            # Step 2: Check for Fabrication Framing
            # User: "What is the GDP?" Bot: "Let's assume it is..."
            found_fabrication = [p for p in self.fabrication_patterns if re.search(p, b_lower)]
            
            if found_fabrication:
                return {
                    "violation": True,
                    "reason": "Grounding Failure: AI used hypothetical framing for a factual query.",
                    "score": 0.7,
                    "metadata": {"markers": found_fabrication}
                }

            # Step 3: Check for Impossible Real-Time Knowledge
            # Simple check to see if it claims "Right Now" knowledge without tools.
            found_cutoff = [p for p in self.cutoff_patterns if re.search(p, b_lower)]
            
            if found_cutoff:
                return {
                    "violation": True,
                    "reason": "Hallucination Risk: AI claimed real-time knowledge (breaking news/prices) without tool use.",
                    "score": 0.6,
                    "metadata": {"markers": found_cutoff}
                }

            return {"violation": False, "reason": "Response appears confident and grounded.", "score": 0.0}

        except Exception as e:
            logger.error(f"Rule 19 Execution Error: {str(e)}")
            return {"violation": False, "reason": "System error.", "score": 0.0}