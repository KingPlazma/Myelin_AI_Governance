import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

logger = logging.getLogger(__name__)

class Rule16PhishingLinks(GovernanceRule):
    """
    GOVERNANCE RULE 16: PHISHING & MALICIOUS LINK AUDITOR
    Scans generated URLs for phishing indicators, suspicious TLDs, 
    and IP-based links. Enforces a 'Safe Domain' preference.
    """
    def __init__(self):
        super().__init__(
            name="Phishing & Malicious Link Auditor", 
            description="Detects suspicious URLs, shortened links, and potential phishing domains.", 
            severity=0.9 
        )
        
        # 1. URL Extraction Pattern (Standard Web URL)
        self.url_pattern = r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'

        # 2. Suspicious TLDs (Top Level Domains often used for spam/malware)
        self.risky_tlds = [
            r"\.xyz", r"\.top", r"\.zip", r"\.tk", r"\.cn", 
            r"\.ga", r"\.cf", r"\.gq", r"\.ml", r"\.mov"
        ]

        # 3. Phishing Keywords in Domain
        self.phishing_keywords = [
            r"login", r"secure", r"verify", r"update", r"account",
            r"banking", r"paypal", r"crypto", r"free-gift"
        ]

        # 4. Obfuscation Patterns
        self.obfuscation_patterns = [
            r"bit\.ly", r"goo\.gl", r"tinyurl", # Shorteners hide the destination
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" # Raw IP Address links (http://192.168.1.5)
        ]

        # 5. Allowlist (Safe Zones)
        # If the link matches these, we ignore other flags.
        self.safe_domains = [
            r"\.gov", r"\.edu", r"\.org", r"wikipedia\.org", 
            r"google\.com", r"microsoft\.com", r"apple\.com", 
            r"amazon\.com", r"github\.com", r"stackoverflow\.com"
        ]

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        try:
            b_lower = bot_response.lower()

            # Step 1: Extract all URLs from the response
            urls_found = re.findall(self.url_pattern, b_lower)
            
            if not urls_found:
                return {"violation": False, "reason": "No URLs detected.", "score": 0.0}

            violations = []

            for url in urls_found:
                # Check Allowlist First (Whitelisting)
                if any(re.search(safe, url) for safe in self.safe_domains):
                    continue

                # Check for Risky TLDs
                if any(re.search(tld + r"(/|$)", url) for tld in self.risky_tlds):
                    violations.append(f"Suspicious TLD: {url}")

                # Check for Raw IPs or Shorteners
                if any(re.search(obf, url) for obf in self.obfuscation_patterns):
                    violations.append(f"Obfuscated/IP Link: {url}")

                # Check for Phishing Keywords (e.g., paypal-secure-login.com)
                # We only check this if it's NOT a major known domain to avoid false positives
                if any(k in url for k in self.phishing_keywords):
                    violations.append(f"Phishing Keyword: {url}")

            if violations:
                return {
                    "violation": True,
                    "reason": f"Security Warning: AI generated suspicious or unsafe links: {violations}",
                    "score": 0.9,
                    "metadata": {"suspicious_urls": violations}
                }

            return {"violation": False, "reason": "URLs appear to be from standard/safe domains.", "score": 0.0}

        except Exception as e:
            logger.error(f"Rule 16 Execution Error: {str(e)}")
            return {"violation": False, "reason": "System error.", "score": 0.0}