"""
Enhanced MYELIN Orchestrator with Custom Rules Support
Extends the original orchestrator to integrate custom rules
"""

import sys
import os
from typing import Dict, List, Optional, Any
import logging

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.myelin_orchestrator import MyelinOrchestrator
from backend.services.rule_engine import get_rule_engine
from backend.services.audit_service import get_audit_service
from backend.models.audit_log import AuditLogCreate

logger = logging.getLogger(__name__)


class EnhancedMyelinOrchestrator(MyelinOrchestrator):
    """
    Enhanced orchestrator with custom rules support
    Extends the base orchestrator to include organization-specific custom rules
    """
    
    def __init__(self):
        super().__init__()
        self.rule_engine = get_rule_engine()
        self.audit_service = get_audit_service()
        logger.info("✅ Enhanced MYELIN Orchestrator initialized with custom rules support")
    
    async def audit_conversation_with_custom_rules(
        self,
        user_input: str,
        bot_response: str,
        source_text: Optional[str] = None,
        organization_id: Optional[str] = None,
        api_key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive audit with custom rules
        
        Args:
            user_input: User's message
            bot_response: AI's response
            source_text: Optional source text for factual verification
            organization_id: Organization ID for custom rules
            api_key_id: API key ID for audit logging
        
        Returns:
            Comprehensive audit report with custom rules
        """
        # Run default audit
        default_result = self.audit_conversation(user_input, bot_response, source_text)
        
        # If no organization_id, return default result only
        if not organization_id:
            return default_result
        
        # Execute custom rules for each pillar
        custom_violations = {
            "toxicity": [],
            "governance": [],
            "bias": []
        }
        
        try:
            # Toxicity custom rules
            toxicity_violations = await self.rule_engine.execute_all_custom_rules(
                organization_id=organization_id,
                pillar="toxicity",
                user_input=user_input,
                bot_response=bot_response
            )
            custom_violations["toxicity"] = toxicity_violations
            
            # Governance custom rules
            governance_violations = await self.rule_engine.execute_all_custom_rules(
                organization_id=organization_id,
                pillar="governance",
                user_input=user_input,
                bot_response=bot_response
            )
            custom_violations["governance"] = governance_violations
            
            # Bias custom rules
            bias_violations = await self.rule_engine.execute_all_custom_rules(
                organization_id=organization_id,
                pillar="bias",
                user_input=user_input,
                bot_response=bot_response
            )
            custom_violations["bias"] = bias_violations
            
        except Exception as e:
            logger.error(f"Error executing custom rules: {e}")
        
        # Merge custom violations with default results
        enhanced_result = self._merge_custom_violations(default_result, custom_violations)
        
        # Log audit if database is available
        if api_key_id:
            try:
                await self._log_audit(
                    organization_id=organization_id,
                    api_key_id=api_key_id,
                    audit_type="conversation",
                    input_data={
                        "user_input": user_input,
                        "bot_response": bot_response,
                        "source_text": source_text
                    },
                    output_data=enhanced_result
                )
            except Exception as e:
                logger.error(f"Error logging audit: {e}")
        
        return enhanced_result
    
    async def audit_toxicity_with_custom_rules(
        self,
        user_input: str,
        bot_response: str,
        organization_id: Optional[str] = None,
        api_key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run toxicity audit with custom rules"""
        
        # Run default audit
        default_result = self.audit_toxicity(user_input, bot_response)
        
        if not organization_id:
            return default_result
        
        # Execute custom toxicity rules
        try:
            custom_violations = await self.rule_engine.execute_all_custom_rules(
                organization_id=organization_id,
                pillar="toxicity",
                user_input=user_input,
                bot_response=bot_response
            )
            
            # Merge violations
            if custom_violations:
                default_violations = default_result.get("report", {}).get("violations", [])
                all_violations = self.rule_engine.merge_violations(default_violations, custom_violations)
                default_result["report"]["violations"] = all_violations
                default_result["report"]["custom_rules_triggered"] = len(custom_violations)
        
        except Exception as e:
            logger.error(f"Error executing custom toxicity rules: {e}")
        
        # Log audit
        if api_key_id:
            try:
                await self._log_audit(
                    organization_id=organization_id,
                    api_key_id=api_key_id,
                    audit_type="toxicity",
                    input_data={"user_input": user_input, "bot_response": bot_response},
                    output_data=default_result
                )
            except Exception as e:
                logger.error(f"Error logging audit: {e}")
        
        return default_result
    
    def _merge_custom_violations(self, default_result: Dict[str, Any], 
                                 custom_violations: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Merge custom rule violations with default audit results"""
        
        enhanced_result = default_result.copy()
        
        # Add custom violations to each pillar
        for pillar, violations in custom_violations.items():
            if violations and pillar in enhanced_result.get("pillars", {}):
                pillar_report = enhanced_result["pillars"][pillar].get("report", {})
                
                # Merge violations
                default_violations = pillar_report.get("violations", [])
                all_violations = self.rule_engine.merge_violations(default_violations, violations)
                pillar_report["violations"] = all_violations
                pillar_report["custom_rules_triggered"] = len(violations)
                
                # Update decision if custom rules found violations
                if violations:
                    # Get highest severity
                    severities = [v.get("severity", "LOW") for v in violations]
                    if "CRITICAL" in severities:
                        pillar_report["decision"] = "BLOCK"
                        pillar_report["risk_level"] = "CRITICAL"
        
        # Update overall decision
        all_custom_violations = []
        for violations in custom_violations.values():
            all_custom_violations.extend(violations)
        
        if all_custom_violations:
            enhanced_result["overall"]["custom_rules_triggered"] = len(all_custom_violations)
            
            # Update risk factors
            risk_factors = enhanced_result["overall"].get("risk_factors", [])
            for violation in all_custom_violations:
                risk_factors.append(f"Custom rule: {violation.get('rule_name', 'Unknown')}")
            enhanced_result["overall"]["risk_factors"] = risk_factors
        
        return enhanced_result
    
    async def _log_audit(self, organization_id: str, api_key_id: str, audit_type: str,
                        input_data: Dict[str, Any], output_data: Dict[str, Any]):
        """Log audit to database"""
        
        # Extract triggered rules
        triggered_rules = []
        if "pillars" in output_data:
            for pillar_data in output_data["pillars"].values():
                violations = pillar_data.get("report", {}).get("violations", [])
                for violation in violations:
                    if "rule_id" in violation:
                        triggered_rules.append(violation["rule_id"])
        
        # Create audit log
        log_data = AuditLogCreate(
            organization_id=organization_id,
            api_key_id=api_key_id,
            audit_type=audit_type,
            input_data=input_data,
            output_data=output_data,
            triggered_rules=triggered_rules,
            overall_decision=output_data.get("overall", {}).get("decision", "ALLOW"),
            risk_level=output_data.get("overall", {}).get("risk_level", "LOW")
        )
        
        await self.audit_service.log_audit(log_data)


# Global enhanced orchestrator instance
_enhanced_orchestrator = None


def get_enhanced_orchestrator() -> EnhancedMyelinOrchestrator:
    """Get or create enhanced orchestrator instance"""
    global _enhanced_orchestrator
    if _enhanced_orchestrator is None:
        _enhanced_orchestrator = EnhancedMyelinOrchestrator()
    return _enhanced_orchestrator

