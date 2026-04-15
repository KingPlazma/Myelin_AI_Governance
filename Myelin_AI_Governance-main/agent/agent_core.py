import sys
import os
import re
import logging
from typing import Dict, List, Optional, Any

# Add orchestrator to path
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_path, "orchestrator"))

try:
    from myelin_orchestrator import MyelinOrchestrator, get_orchestrator
except ImportError as e:
    logger.error(f"Failed to import myelin_orchestrator: {e}")
    raise

logger = logging.getLogger("MyelinAgentCore")

class MyelinAgentCore(MyelinOrchestrator):
    """
    The 'Brain' of the 24/7 Agent.
    Extends MyelinOrchestrator with autonomous remediation (fixing) capabilities.
    """
    
    def __init__(self):
        super().__init__()
        logger.info("🚀 Myelin Agent Core Brain Initialized")

    def remediate(self, text: str, audit_results: Dict[str, Any]) -> str:
        """
        Autonomously fixes problematic content based on audit results.
        Instead of just blocking, the agent 'remedies' the response.
        """
        remediated_text = text
        decision = audit_results.get("overall", {}).get("decision", "ALLOW")
        
        if decision == "ALLOW":
            return text

        logger.info(f"🛠 Agent Remediation triggered for decision: {decision}")

        # 1. PILLAR-SPECIFIC REMEDIATION
        pillars = audit_results.get("pillars", {})

        # --- GOVERNANCE REMEDIATION (PII Redaction) ---
        gov_report = pillars.get("governance", {}).get("report", {})
        if gov_report.get("governance_risk_score", 0) > 0.5:
            logger.info("🛡 Remedying Governance Violation (PII Redaction)")
            remediated_text = self._redact_pii(remediated_text)

        # --- TOXICITY REMEDIATION ---
        tox_report = pillars.get("toxicity", {}).get("report", {})
        if tox_report.get("decision") == "BLOCK" or tox_report.get("toxicity_score", 0) > 0.6:
             logger.info("⚠️ Remedying Toxicity Violation")
             remediated_text = "[REDACTED BY MYELIN AGENT: Harmful or toxic content detected in AI response]"

        # --- FACTUAL REMEDIATION (Hallucination Warning) ---
        fact_report = pillars.get("factual", {})
        if fact_report.get("status") == "success":
            score = fact_report.get("final_score", 1.0)
            if score < 0.5:
                logger.info("🔍 Remedying Factual Inconsistency")
                remediated_text = f"⚠️ [MYELIN AGENT WARNING: The following response may contain factual hallucinations] \n\n{remediated_text}"

        return remediated_text

    def _redact_pii(self, text: str) -> str:
        """Helper to redact sensitive patterns if the pillar flags it"""
        # Simple regex fallbacks for the agent's immediate remediation
        patterns = {
            r'\b\d{3}-\d{2}-\d{4}\b': "[SSN-REDACTED]",
            r'\b(?:\d{4}-){3}\d{4}\b': "[CREDIT-CARD-REDACTED]",
            r'\b\d{16}\b': "[CREDIT-CARD-REDACTED]",
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': "[EMAIL-REDACTED]",
            r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b': "[PHONE-REDACTED]"
        }
        
        result = text
        for pattern, replacement in patterns.items():
            result = re.sub(pattern, replacement, result)
        
        return result

# Singleton for the agent
_agent_instance = None

def get_agent_core() -> MyelinAgentCore:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MyelinAgentCore()
    return _agent_instance
