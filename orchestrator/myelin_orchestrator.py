"""
MYELIN Orchestrator - Unified AI Governance Engine
Integrates all 4 pillars: Fairness, Factual Check, Toxicity, and Governance
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MyelinOrchestrator")


class MyelinOrchestrator:
    """
    Central orchestrator that coordinates all MYELIN pillars.
    Provides a unified interface for AI governance auditing.
    """
    
    def __init__(self):
        """Initialize all pillar modules"""
        self.fairness_module = None
        self.factual_module = None
        self.toxicity_module = None
        self.governance_module = None
        self.bias_module = None
        
        self._initialize_modules()
    
    def _initialize_modules(self):
        """Dynamically load all pillar modules with graceful error handling"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Store original sys.path to restore after each pillar
        original_path = sys.path.copy()
        
        # Fairness Pillar
        try:
            fairness_path = os.path.join(base_path, "Myelin_Fairness_Pillar_RICH_FINAL")
            sys.path.insert(0, fairness_path)
            from ensemble import FairnessEnsemble
            self.fairness_module = FairnessEnsemble(os.path.join(fairness_path, "rules"))
            logger.info("✅ Fairness Pillar loaded")
        except Exception as e:
            logger.warning(f"⚠️  Fairness Pillar failed to load: {e}")
            self.fairness_module = self._create_mock_fairness()
            
        # Factual Check Pillar (FCAM)
        try:
            fcam_path = os.path.join(base_path, "FCAM_fixed", "FCAM_fixed", "Factual_Consistency_Accountability_Module")
            sys.path.insert(0, fcam_path)
            sys.path.insert(0, os.path.join(fcam_path, "modules"))
            
            # Import all FCAM rules
            from modules.factual.rules.rule_01_source_alignment import SourceAlignmentRule
            from modules.factual.rules.rule_02_atomic_claims import AtomicClaimDecompositionRule
            from modules.factual.rules.rule_03_claim_verification import ClaimLevelVerificationRule
            from modules.factual.rules.rule_04_qa_consistency import QABasedConsistencyRule
            from modules.factual.rules.rule_05_coverage import CoverageCompletenessRule
            from modules.factual.rules.rule_06_stability import MetamorphicStabilityRule
            from modules.factual.rules.rule_07_multilingual_consistency import MultilingualConsistencyRule
            from modules.factual.rules.rule_08_external_knowledge import ExternalKnowledgeVerificationRule
            from modules.factual.rules.rule_09_token_validation import TokenValidationRule
            from modules.factual.rules.rule_10_token_correction import TokenCorrectionRule
            from modules.factual.rules.rule_11_numerical_consistency import NumericalConsistencyRule
            from modules.factual.rules.rule_12_temporal_consistency import TemporalConsistencyRule
            from modules.factual.rules.rule_13_entity_consistency import EntityConsistencyRule
            from modules.factual.rules.rule_14_causal_consistency import CausalConsistencyRule
            from modules.factual.rules.rule_15_internal_consistency import InternalConsistencyRule
            from modules.factual.rules.rule_16_severity import HallucinationSeverityRule
            from modules.factual.rules.rule_17_uncertainty import UncertaintySignalingRule
            from modules.factual.rules.rule_18_cross_model import CrossModelAgreementRule
            from modules.factual.rules.rule_19_domain_sensitivity import DomainSensitivityRule
            from modules.factual.rules.rule_20_final_decision import FinalFactualConfidenceRule
            from modules.factual.ensemble_manager import FactualEnsembleManager
            
            fcam_rules = [
                SourceAlignmentRule(),
                AtomicClaimDecompositionRule(),
                ClaimLevelVerificationRule(),
                QABasedConsistencyRule(),
                CoverageCompletenessRule(),
                MetamorphicStabilityRule(),
                MultilingualConsistencyRule(),
                ExternalKnowledgeVerificationRule(),
                TokenValidationRule(),
                TokenCorrectionRule(),
                NumericalConsistencyRule(),
                TemporalConsistencyRule(),
                EntityConsistencyRule(),
                CausalConsistencyRule(),
                InternalConsistencyRule(),
                HallucinationSeverityRule(),
                UncertaintySignalingRule(),
                CrossModelAgreementRule(),
                DomainSensitivityRule()
            ]
            
            self.factual_module = FactualEnsembleManager(fcam_rules)
            self.factual_meta_rule = FinalFactualConfidenceRule()
            logger.info("✅ Factual Check Pillar (FCAM) loaded")
        except Exception as e:
            logger.warning(f"⚠️  Factual Check Pillar failed to load: {e}")
            self.factual_module = self._create_mock_factual()
            self.factual_meta_rule = None
            
        # Toxicity Pillar
        try:
            sys.path = original_path.copy()  # Reset path
            toxicity_path = os.path.join(base_path, "Toxicity", "Toxicity")
            if toxicity_path not in sys.path:
                sys.path.insert(0, toxicity_path)
            
            # Clear any cached modules
            if 'modules.toxicity' in sys.modules:
                del sys.modules['modules.toxicity']
            if 'modules.toxicity.ensemble_manager' in sys.modules:
                del sys.modules['modules.toxicity.ensemble_manager']
            
            from modules.toxicity.ensemble_manager import ToxicityEnsembleManager
            self.toxicity_module = ToxicityEnsembleManager()
            logger.info("✅ Toxicity Pillar loaded")
        except Exception as e:
            logger.warning(f"⚠️  Toxicity Pillar failed to load: {e}")
            self.toxicity_module = self._create_mock_toxicity()
            
        # Governance Pillar
        try:
            sys.path = original_path.copy()  # Reset path
            governance_path = os.path.join(base_path, "Governance_Project", "Governance_Project")
            if governance_path not in sys.path:
                sys.path.insert(0, governance_path)
            
            # Clear any cached modules
            if 'modules.governance' in sys.modules:
                del sys.modules['modules.governance']
            if 'modules.governance.ensemble_manager' in sys.modules:
                del sys.modules['modules.governance.ensemble_manager']
            
            from modules.governance.ensemble_manager import GovernanceEnsembleManager
            self.governance_module = GovernanceEnsembleManager()
            logger.info("✅ Governance Pillar loaded")
        except Exception as e:
            logger.warning(f"⚠️  Governance Pillar failed to load: {e}")
            self.governance_module = self._create_mock_governance()
        
        # Bias Pillar
        try:
            sys.path = original_path.copy()  # Reset path
            bias_path = os.path.join(base_path, "BIAS", "mylin")
            if bias_path not in sys.path:
                sys.path.insert(0, bias_path)
            
            # Clear any cached modules
            if 'modules.bias' in sys.modules:
                del sys.modules['modules.bias']
            if 'modules.bias.ensemble_manager' in sys.modules:
                del sys.modules['modules.bias.ensemble_manager']
            
            from modules.bias.ensemble_manager import BiasEnsembleManager
            self.bias_module = BiasEnsembleManager()
            logger.info("✅ Bias Pillar loaded")
        except Exception as e:
            logger.warning(f"⚠️  Bias Pillar failed to load: {e}")
            self.bias_module = self._create_mock_bias()
            
        logger.info("🎯 MYELIN orchestrator initialized!")
    
    def _create_mock_fairness(self):
        """Create mock fairness module"""
        class MockFairness:
            def run(self, y_true, y_pred, sensitive):
                return {
                    "module": "fairness",
                    "overall_score": 0.0,
                    "verdict": "MOCK_MODE",
                    "rules": [],
                    "note": "Fairness pillar not available - install dependencies"
                }
        return MockFairness()
    
    def _create_mock_factual(self):
        """Create mock factual module"""
        class MockFactual:
            def evaluate(self, model_output, source_text=None):
                return 0.5, {"note": "Factual pillar not available - install dependencies"}
        return MockFactual()
    
    def _create_mock_toxicity(self):
        """Create mock toxicity module"""
        class MockToxicity:
            def run_full_audit(self, user_input, bot_response):
                return {
                    "module": "toxicity",
                    "toxicity_score": 0.0,
                    "risk_level": "MOCK_MODE",
                    "decision": "ALLOW",
                    "violated_categories": [],
                    "violations": [],
                    "details": [],
                    "note": "Toxicity pillar not available - install dependencies"
                }
        return MockToxicity()
    
    def _create_mock_governance(self):
        """Create mock governance module"""
        class MockGovernance:
            def run_full_audit(self, user_input, bot_response):
                return {
                    "governance_risk_score": 0.0,
                    "details": [],
                    "note": "Governance pillar not available - install dependencies"
                }
        return MockGovernance()
    
    def _create_mock_bias(self):
        """Create mock bias module"""
        class MockBias:
            def run_full_audit(self, user_input, bot_response):
                return {
                    "module": "bias",
                    "bias_score": 0.0,
                    "risk_level": "MOCK_MODE",
                    "decision": "ALLOW",
                    "violations": [],
                    "details": [],
                    "note": "Bias pillar not available - install dependencies"
                }
        return MockBias()
    
    def audit_fairness(
        self, 
        y_true: List[int], 
        y_pred: List[int], 
        sensitive: List[int]
    ) -> Dict[str, Any]:
        """
        Run fairness audit on ML model predictions
        
        Args:
            y_true: Ground truth labels
            y_pred: Model predictions
            sensitive: Sensitive attribute (0=privileged, 1=unprivileged)
            
        Returns:
            Fairness audit report
        """
        try:
            report = self.fairness_module.run(
                y_true=y_true,
                y_pred=y_pred,
                sensitive=sensitive
            )
            return {
                "status": "success",
                "pillar": "fairness",
                "timestamp": datetime.utcnow().isoformat(),
                "report": report
            }
        except Exception as e:
            logger.error(f"Fairness audit failed: {e}")
            return {
                "status": "error",
                "pillar": "fairness",
                "error": str(e)
            }
    
    def audit_factual(
        self, 
        model_output: str, 
        source_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run factual consistency check on AI-generated content
        
        Args:
            model_output: The AI-generated text to verify
            source_text: Optional source/reference text
            
        Returns:
            Factual consistency report
        """
        try:
            final_score, report = self.factual_module.evaluate(
                model_output=model_output,
                source_text=source_text
            )
            
            # Apply meta rule if available
            meta_score = None
            meta_report = None
            if self.factual_meta_rule:
                meta_score, meta_report = self.factual_meta_rule.evaluate(
                    model_output=model_output,
                    source_text=source_text,
                    final_score=final_score
                )
            
            return {
                "status": "success",
                "pillar": "factual",
                "timestamp": datetime.utcnow().isoformat(),
                "final_score": round(final_score, 3),
                "meta_score": meta_score,
                "meta_decision": meta_report,
                "detailed_report": report
            }
        except Exception as e:
            logger.error(f"Factual audit failed: {e}")
            return {
                "status": "error",
                "pillar": "factual",
                "error": str(e)
            }
    
    def audit_toxicity(
        self, 
        user_input: str, 
        bot_response: str
    ) -> Dict[str, Any]:
        """
        Run toxicity audit on conversation
        
        Args:
            user_input: User's message
            bot_response: AI's response
            
        Returns:
            Toxicity audit report
        """
        try:
            report = self.toxicity_module.run_full_audit(user_input, bot_response)
            return {
                "status": "success",
                "pillar": "toxicity",
                "timestamp": datetime.utcnow().isoformat(),
                "report": report
            }
        except Exception as e:
            logger.error(f"Toxicity audit failed: {e}")
            return {
                "status": "error",
                "pillar": "toxicity",
                "error": str(e)
            }
    
    def audit_governance(
        self, 
        user_input: str, 
        bot_response: str
    ) -> Dict[str, Any]:
        """
        Run governance compliance audit
        
        Args:
            user_input: User's message
            bot_response: AI's response
            
        Returns:
            Governance audit report
        """
        try:
            report = self.governance_module.run_full_audit(user_input, bot_response)
            return {
                "status": "success",
                "pillar": "governance",
                "timestamp": datetime.utcnow().isoformat(),
                "report": report
            }
        except Exception as e:
            logger.error(f"Governance audit failed: {e}")
            return {
                "status": "error",
                "pillar": "governance",
                "error": str(e)
            }
    
    def audit_bias(
        self, 
        user_input: str, 
        bot_response: str
    ) -> Dict[str, Any]:
        """
        Run bias detection audit
        
        Args:
            user_input: User's message
            bot_response: AI's response
            
        Returns:
            Bias audit report
        """
        try:
            report = self.bias_module.run_full_audit(user_input, bot_response)
            return {
                "status": "success",
                "pillar": "bias",
                "timestamp": datetime.utcnow().isoformat(),
                "report": report
            }
        except Exception as e:
            logger.error(f"Bias audit failed: {e}")
            return {
                "status": "error",
                "pillar": "bias",
                "error": str(e)
            }
    
    def audit_conversation(
        self, 
        user_input: str, 
        bot_response: str,
        source_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive audit on a conversation (all applicable pillars)
        
        Args:
            user_input: User's message
            bot_response: AI's response
            source_text: Optional source text for factual verification
            
        Returns:
            Comprehensive audit report from all pillars
        """
        logger.info(f"Running comprehensive audit...")
        
        results = {
            "audit_type": "conversation",
            "timestamp": datetime.utcnow().isoformat(),
            "input": {
                "user": user_input,
                "bot": bot_response,
                "source": source_text
            },
            "pillars": {}
        }
        
        # Run Toxicity Check
        toxicity_result = self.audit_toxicity(user_input, bot_response)
        results["pillars"]["toxicity"] = toxicity_result
        
        # Run Governance Check
        governance_result = self.audit_governance(user_input, bot_response)
        results["pillars"]["governance"] = governance_result
        
        # Run Bias Check
        bias_result = self.audit_bias(user_input, bot_response)
        results["pillars"]["bias"] = bias_result
        
        # Run Factual Check (if source provided or on bot response)
        factual_result = self.audit_factual(bot_response, source_text)
        results["pillars"]["factual"] = factual_result
        
        # Calculate overall risk score
        risk_score = 0.0
        risk_factors = []
        
        if toxicity_result["status"] == "success":
            tox_score = toxicity_result["report"].get("toxicity_score", 0)
            risk_score += tox_score * 0.35  # 35% weight
            if tox_score > 0.5:
                risk_factors.append(f"High toxicity detected ({tox_score})")
        
        if governance_result["status"] == "success":
            gov_score = governance_result["report"].get("governance_risk_score", 0)
            risk_score += gov_score * 0.25  # 25% weight
            if gov_score > 0.5:
                risk_factors.append(f"Governance violations ({gov_score})")
        
        if bias_result["status"] == "success":
            bias_score = bias_result["report"].get("bias_score", 0)
            risk_score += bias_score * 0.20  # 20% weight
            if bias_score > 0.5:
                risk_factors.append(f"Bias detected ({bias_score})")
        
        if factual_result["status"] == "success":
            fact_score = 1 - factual_result.get("final_score", 1.0)  # Invert (lower is worse)
            risk_score += fact_score * 0.20  # 20% weight
            if fact_score > 0.5:
                risk_factors.append(f"Low factual accuracy ({factual_result.get('final_score', 0)})")
        
        # Determine overall decision
        if risk_score >= 0.7:
            decision = "BLOCK"
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            decision = "WARN"
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            decision = "REVIEW"
            risk_level = "MEDIUM"
        else:
            decision = "ALLOW"
            risk_level = "LOW"
        
        results["overall"] = {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "decision": decision,
            "risk_factors": risk_factors
        }
        
        logger.info(f"Audit complete: {decision} (risk: {risk_level})")
        return results
    
    def audit_ml_model(
        self,
        y_true: List[int],
        y_pred: List[int],
        sensitive: List[int]
    ) -> Dict[str, Any]:
        """
        Run fairness audit on ML model
        
        Args:
            y_true: Ground truth labels
            y_pred: Model predictions
            sensitive: Sensitive attributes
            
        Returns:
            ML model fairness report
        """
        logger.info("Running ML model fairness audit...")
        
        results = {
            "audit_type": "ml_model",
            "timestamp": datetime.utcnow().isoformat(),
            "pillars": {}
        }
        
        # Run Fairness Check
        fairness_result = self.audit_fairness(y_true, y_pred, sensitive)
        results["pillars"]["fairness"] = fairness_result
        
        # Overall assessment
        if fairness_result["status"] == "success":
            verdict = fairness_result["report"].get("verdict", "UNKNOWN")
            overall_score = fairness_result["report"].get("overall_score", 0)
            
            results["overall"] = {
                "verdict": verdict,
                "fairness_score": overall_score,
                "is_fair": verdict == "PASS"
            }
        else:
            results["overall"] = {
                "verdict": "ERROR",
                "error": fairness_result.get("error")
            }
        
        return results


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> MyelinOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MyelinOrchestrator()
    return _orchestrator_instance


if __name__ == "__main__":
    # Test the orchestrator
    print("\n" + "="*80)
    print(" MYELIN ORCHESTRATOR - INTEGRATION TEST ".center(80, "="))
    print("="*80 + "\n")
    
    orchestrator = get_orchestrator()
    
    # Test 1: Conversation Audit
    print("\n[TEST 1] Conversation Audit")
    print("-" * 80)
    result = orchestrator.audit_conversation(
        user_input="Tell me about climate change",
        bot_response="Climate change is a hoax invented by idiots. Everyone who believes it is stupid.",
        source_text="Climate change refers to long-term shifts in temperatures and weather patterns."
    )
    print(f"Decision: {result['overall']['decision']}")
    print(f"Risk Level: {result['overall']['risk_level']}")
    print(f"Risk Score: {result['overall']['risk_score']}")
    
    # Test 2: ML Model Fairness
    print("\n[TEST 2] ML Model Fairness Audit")
    print("-" * 80)
    result = orchestrator.audit_ml_model(
        y_true=[1, 1, 1, 1, 0, 0, 0, 0],
        y_pred=[1, 1, 0, 1, 1, 0, 0, 0],
        sensitive=[0, 0, 0, 0, 1, 1, 1, 1]
    )
    print(f"Verdict: {result['overall']['verdict']}")
    print(f"Fairness Score: {result['overall'].get('fairness_score', 'N/A')}")
    
    print("\n" + "="*80)
    print(" INTEGRATION TEST COMPLETE ".center(80, "="))
    print("="*80 + "\n")

