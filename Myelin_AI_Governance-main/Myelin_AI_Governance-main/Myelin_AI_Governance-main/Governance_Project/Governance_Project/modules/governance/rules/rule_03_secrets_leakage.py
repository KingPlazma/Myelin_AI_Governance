import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

logger = logging.getLogger(__name__)

class Rule03SecretsLeakage(GovernanceRule):
    def __init__(self):
        super().__init__(
            name="Secrets & Credentials Leakage Auditor", 
            description="Detects exposure of cloud credentials, private keys, and API tokens.", 
            severity=1.0
        )
        
        # Regex patterns for common secrets
        self.patterns = {
            "AWS Access Key": r'\bAKIA[0-9A-Z]{16}\b',
            "Google API Key": r'\bAIza[0-9A-Za-z-_]{35}\b',
            "Slack Bot Token": r'xoxb-[0-9]{10,12}-[0-9a-zA-Z]{24}',
            "Private Key Block": r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----',
            "Generic API Key": r'\b[a-zA-Z0-9]{32,45}\b',
            "Bearer Token": r'Bearer\s[a-zA-Z0-9\-\._~\+\/]+'
        }

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        try:
            leaks_found = {}
            total_hits = 0

            for secret_type, pattern in self.patterns.items():
                matches = re.findall(pattern, bot_response)
                
                # Filter for Generic Keys to avoid false positives on normal words
                if secret_type == "Generic API Key":
                    # Only count if it has at least one number AND one letter
                    matches = [m for m in matches if any(c.isdigit() for c in m) and any(c.isalpha() for c in m)]

                if matches:
                    leaks_found[secret_type] = len(matches)
                    total_hits += len(matches)

            if total_hits > 0:
                return {
                    "violation": True,
                    "reason": f"CRITICAL: Secrets Leakage. Found {total_hits} potential credentials exposed.",
                    "score": 1.0,
                    "metadata": {
                        "exposed_types": leaks_found,
                        "compliance_standard": "SOC2 / ISO 27001"
                    }
                }

            return {"violation": False, "reason": "No credentials detected.", "score": 0.0}

        except Exception as e:
            logger.error(f"Rule 03 Execution Error: {str(e)}")
            return {"violation": False, "reason": "System error.", "score": 0.0}