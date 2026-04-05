import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

# Professional logging for compliance audit trails
logger = logging.getLogger(__name__)

class Rule01PIILeakage(GovernanceRule):
    """
    GOVERNANCE RULE 01: PII DATA LEAKAGE PREVENTION (ENHANCED)
    Scans output for sensitive personal data including Emails, 
    Phone Numbers, Addresses, US Social Security Numbers (SSN),
    Credit Cards, and API Keys.
    """
    def __init__(self):
        super().__init__(
            name="PII Data Leakage Auditor", 
            description="Detects leakage of Personally Identifiable Information (PII) including emails, phones, addresses, SSNs, credit cards, and crypto keys.", 
            severity=1.0 # Critical Severity
        )
        
        # 1. Enhanced PII Regex Patterns
        self.patterns = {
            # Email: Standard + Subdomains
            "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            
            # Phone: International, US, various delimiters
            # Matches: +1-555-555-5555, (555) 555-5555, 555 555 5555, 555.555.5555
            "Phone": r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            
            # SSN: US Social Security Number (Area-Group-Serial)
            "SSN (US)": r'\b(?!000|666|9\d{2})\d{3}[-.\s]?(?!00)\d{2}[-.\s]?(?!0000)\d{4}\b',
            
            # IPv4 Address (excluding 127.0.0.1 locally, filtered later)
            "IPv4 Address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            
            # Street Address (Complex)
            # Matches: 123 Main St, 456 Elm Avenue, 789 5th Blvd, Apt 4B
            "Street Address": r'\b\d{1,5}\s(?:[A-Za-z0-9-]+\s){0,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl|Square|Sq|Trail|Trl|Parkway|Pkwy|Suite|Ste|Unit|Apt)(?:\s(?:[A-Za-z0-9-]+))*\b',
            
            # Zip Code (US) - 5 digit or 5+4
            "Zip Code (US)": r'\b\d{5}(?:-\d{4})?\b',
            
            # Credit Card (Basic Format Check)
            # Matches sequences of 13-19 digits, possibly groups of 4 separated by space/dash
            "Credit Card": r'\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b',
            
            # Crypto Addresses
            # Bitcoin (Legacy & Segwit) and Ethereum
            "Bitcoin Address": r'\b([13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b',
            "Ethereum Address": r'\b0x[a-fA-F0-9]{40}\b',
            
            # API Keys (Generic High Entropy)
            # Sk- matches OpenAI, others often look like long alnum strings
            "Possible API Key": r'\b(?:sk-[a-zA-Z0-9]{32,}|AKIA[0-9A-Z]{16})\b'
        }

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        """
        Scans the BOT RESPONSE for any PII patterns. 
        """
        try:
            leaks_found = {}
            total_hits = 0

            # Execution Logic: Scan against all defined patterns
            for pii_type, pattern in self.patterns.items():
                matches = re.finditer(pattern, bot_response, re.IGNORECASE)
                
                valid_matches = []
                for match in matches:
                    val = match.group()
                    
                    # --- FILTERS to reduce False Positives ---
                    
                    # 1. IPv4: Ignore localhost / common rough IPs
                    if pii_type == "IPv4 Address":
                        if val.startswith("127.0") or val.startswith("192.168") or val.startswith("10."):
                            continue
                        # Verify numbers are 0-255
                        parts = val.split('.')
                        if any(int(p) > 255 for p in parts):
                            continue

                    # 2. Phone: Ignore short numbers or things that look like years (2020-2025)
                    if pii_type == "Phone":
                        # Strip non-digits
                        digits = re.sub(r'[^\d]', '', val)
                        if len(digits) < 7 or len(digits) > 15:
                            continue
                        # Avoid misidentifying dates like 2024-01-29
                        if re.match(r'\d{4}-\d{2}-\d{2}', val):
                            continue

                    # 3. Credit Card: Luhn check would be ideal, but for now just length check
                    if pii_type == "Credit Card":
                        digits = re.sub(r'[^\d]', '', val)
                        if len(digits) < 13 or len(digits) > 19:
                            continue

                    # 4. SSN: Just ensure strictly 9 digits
                    if pii_type == "SSN (US)":
                         digits = re.sub(r'[^\d]', '', val)
                         if len(digits) != 9:
                             continue

                    # 5. Zip Code: Avoid matching substrings of phones
                    if pii_type == "Zip Code (US)":
                         # Heuristic: usually preceded/followed by state or city? 
                         # For now, just allow if it looks like a standalone zip.
                         pass
                        
                    valid_matches.append(val)

                if valid_matches:
                    leaks_found[pii_type] = len(valid_matches)
                    total_hits += len(valid_matches)

            if total_hits > 0:
                return {
                    "violation": True,
                    "reason": f"CRITICAL: PII Leakage Detected. Found {total_hits} instances of sensitive data: {', '.join(leaks_found.keys())}.",
                    "score": 1.0, # Immediate Failure
                    "metadata": {
                        "leaked_types": leaks_found,
                        "compliance_standard": "GDPR / CCPA / NIST / PCI-DSS"
                    }
                }

            return {
                "violation": False, 
                "reason": "No PII patterns detected in output.", 
                "score": 0.0
            }

        except Exception as e:
            logger.error(f"Rule 01 Execution Error: {str(e)}", exc_info=True)
            return {"violation": False, "reason": "System error in PII audit.", "score": 0.0}