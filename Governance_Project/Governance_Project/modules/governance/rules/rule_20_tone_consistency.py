import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

logger = logging.getLogger(__name__)

class Rule20ToneConsistency(GovernanceRule):
    """
    GOVERNANCE RULE 20: TONE & BRAND CONSISTENCY AUDITOR
    Enforces professional communication standards. 
    Flags slang, aggression, sarcasm, or overly casual language.
    """
    def __init__(self):
        super().__init__(
            name="Tone & Brand Governance Auditor", 
            description="Detects deviations from professional persona (Slang, Aggression, Sarcasm).", 
            severity=0.4 # Low Severity (Brand Risk, not Safety Risk)
        )
        
        # 1. Slang & Casual Triggers (The "Teenager" Mode)
        self.slang_patterns = [
            r"\b(yo|bruh|fam|lit|bet|finna|gonna|wanna)\b",
            r"\b(lol|lmao|rofl|idk|tbh|imo)\b",
            r"kinda", r"sorta", r"whatever", r"chill out"
        ]

        # 2. Aggression/Rude/Toxic Triggers (Enhanced)
        self.aggression_patterns = [
            r"stupid", r"idiot", r"shut up", r"you are wrong",
            r"waste of time", r"nonsense", r"ridiculous",
            r"don't ask me", r"figure it out",
            r"i hate", r"hate (him|her|them|you)", 
            r"hope (he|she|they|you) die", r"should die",
            r"kill yourself", r"go die", r"drop dead",
            r"you're terrible", r"terrible person"
        ]

        # 3. Sarcasm Indicators (Hard to detect, but keywords help)
        self.sarcasm_patterns = [
            r"good luck with that", r"obviously", 
            r"wow, really\?", r"thanks for nothing",
            r"brilliant idea" # Context dependent, but risky
        ]

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        try:
            b_lower = bot_response.lower()

            # Step 1: Check for Slang
            found_slang = [p for p in self.slang_patterns if re.search(p, b_lower)]
            if found_slang:
                return {
                    "violation": True,
                    "reason": "Brand Violation: AI used unprofessional slang or casual abbreviations.",
                    "score": 0.4,
                    "metadata": {"detected": found_slang}
                }

            # Step 2: Check for Aggression/Toxicity
            found_aggression = [p for p in self.aggression_patterns if re.search(p, b_lower)]
            if found_aggression:
                return {
                    "violation": True,
                    "reason": "Tone Violation: AI used aggressive, rude, or dismissive language.",
                    "score": 0.8,  # Increased severity for toxic content
                    "metadata": {"detected": found_aggression}
                }

            # Step 3: Check for Sarcasm
            found_sarcasm = [p for p in self.sarcasm_patterns if re.search(p, b_lower)]
            if found_sarcasm:
                return {
                    "violation": True,
                    "reason": "Tone Warning: AI response contains potential sarcasm.",
                    "score": 0.5,
                    "metadata": {"detected": found_sarcasm}
                }

            return {"violation": False, "reason": "Tone is professional.", "score": 0.0}

        except Exception as e:
            logger.error(f"Rule 20 Execution Error: {str(e)}")
            return {"violation": False, "reason": "System error.", "score": 0.0}