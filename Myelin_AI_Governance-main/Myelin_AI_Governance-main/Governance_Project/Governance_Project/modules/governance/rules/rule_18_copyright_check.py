import re
import logging
from modules.governance.base_governance_rule import GovernanceRule

logger = logging.getLogger(__name__)

class Rule18CopyrightCheck(GovernanceRule):
    """
    GOVERNANCE RULE 18: COPYRIGHT & IP INFRINGEMENT AUDITOR
    Detects potential plagiarism by scanning for copyright watermarks,
    licensing headers, and ownership claims in the AI output.
    """
    def __init__(self):
        super().__init__(
            name="Copyright & IP Auditor", 
            description="Detects copyright notices, license headers, and IP markers to prevent infringement.", 
            severity=0.8 
        )
        
        # 1. Direct Copyright Markers (The "Watermark")
        # Matches: "Copyright 2023", "(c) John Doe", "All rights reserved"
        self.copyright_patterns = [
            r"copyright\s+(\(c\)|©)?\s*\d{4}",
            r"©\s*\d{4}",
            r"all rights reserved",
            r"reproduction prohibited",
            r"proprietary material",
            r"authorized use only"
        ]

        # 2. Software License Headers (The Code Copy)
        # If AI spits out a full GPL license, it might be copying a specific repo.
        self.license_patterns = [
            r"gnu general public license",
            r"licensed under the apache",
            r"mit license",
            r"creative commons attribution"
        ]

        # 3. Source Watermarks (The "Regurgitation")
        # Common text found in scraped data.
        self.watermark_patterns = [
            r"getty images", r"shutterstock", r"associated press",
            r"reuters", r"bloomberg", r"new york times"
        ]

    def evaluate(self, user_input: str, bot_response: str) -> dict:
        try:
            b_lower = bot_response.lower()

            # Step 1: Check for Copyright Notices
            found_notices = [p for p in self.copyright_patterns if re.search(p, b_lower)]
            
            # Step 2: Check for Software Licenses
            found_licenses = [p for p in self.license_patterns if re.search(p, b_lower)]
            
            # Step 3: Check for Media Watermarks
            found_watermarks = [p for p in self.watermark_patterns if re.search(p, b_lower)]

            violations = found_notices + found_licenses + found_watermarks

            if violations:
                return {
                    "violation": True,
                    "reason": "IP Violation: AI output contains copyright notices or license headers (Potential Plagiarism).",
                    "score": 0.8,
                    "metadata": {
                        "detected_markers": violations,
                        "status": "Potential Infringement"
                    }
                }

            return {
                "violation": False, 
                "reason": "No copyright or IP markers detected.", 
                "score": 0.0
            }

        except Exception as e:
            logger.error(f"Rule 18 Execution Error: {str(e)}")
            return {"violation": False, "reason": "System error.", "score": 0.0}