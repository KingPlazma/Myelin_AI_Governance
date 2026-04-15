import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

# Professional logging for compliance audit trails
logger = logging.getLogger(__name__)

class Rule02FinancialLeakage(GovernanceRule):
    """
    GOVERNANCE RULE 02: FINANCIAL DATA LEAKAGE PREVENTION
    Detects exposure of Credit Card numbers (PCI-DSS), IBANs, 
    and Crypto Wallet addresses.
    """
    def __init__(self):
        super().__init__(
            name="Financial Information Leakage Auditor", 
            description="Detects leakage of sensitive financial data (Credit Cards, IBANs, Crypto Wallets).", 
            severity=1.0 # Critical: Immediate compliance violation
        )
        
        # 1. Financial Regex Patterns
        # Note: These are 'tight' regexes to avoid matching random long numbers
        self.patterns = {
            "Visa Card": r'\b4[0-9]{12}(?:[0-9]{3})?\b',
            "MasterCard": r'\b5[1-5][0-9]{14}\b',
            "Amex Card": r'\b3[47][0-9]{13}\b',
            "IBAN (Generic)": r'\b[A-Z]{2}[0-9]{2}[a-zA-Z0-9]{4}[0-9]{7}([a-zA-Z0-9]?){0,16}\b',
            "Bitcoin Address": r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b',
            "Ethereum Address": r'\b0x[a-fA-F0-9]{40}\b'
        }

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        """
        Scans the output for financial identifiers.
        """
        try:
            leaks_found = {}
            total_hits = 0

            # Execution Logic: Iterate through all financial patterns
            for data_type, pattern in self.patterns.items():
                matches = re.findall(pattern, bot_response)
                
                # Validation Step: Filter out obviously false matches (like test numbers)
                # In a real production system, you would run a Luhn Checksum here.
                # For this project, we filter out common placeholders like '0000...'
                valid_matches = [m for m in matches if not re.match(r'^[0]+$', m)]
                
                if valid_matches:
                    leaks_found[data_type] = len(valid_matches)
                    total_hits += len(valid_matches)

            if total_hits > 0:
                return {
                    "violation": True,
                    "reason": f"CRITICAL: Financial Data Leakage. Found {total_hits} instances of financial identifiers.",
                    "score": 1.0,
                    "metadata": {
                        "leaked_types": leaks_found,
                        "compliance_standard": "PCI-DSS / AML"
                    }
                }

            return {
                "violation": False, 
                "reason": "No financial data patterns detected.", 
                "score": 0.0
            }

        except Exception as e:
            logger.error(f"Rule 02 Execution Error: {str(e)}", exc_info=True)
            return {"violation": False, "reason": "System error in Financial audit.", "score": 0.0}