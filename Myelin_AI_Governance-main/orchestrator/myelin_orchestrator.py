"""
MYELIN Orchestrator - Unified AI Governance Engine
Integrates all 4 pillars: Fairness, Factual Check, Toxicity, and Governance
"""

import sys
import os
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Protocol, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MyelinOrchestrator")


class FairnessModule(Protocol):
    def run(self, y_true: List[int], y_pred: List[int], sensitive: List[int]) -> Dict[str, Any]:
        ...


class FactualModule(Protocol):
    def evaluate(self, model_output: str, source_text: Optional[str] = None) -> Tuple[float, Dict[str, Any]]:
        ...


class FactualMetaRule(Protocol):
    def evaluate(
        self,
        model_output: str,
        source_text: Optional[str] = None,
        final_score: Optional[float] = None,
    ) -> Tuple[float, Any]:
        ...


class ConversationAuditModule(Protocol):
    def run_full_audit(self, user_input: str, bot_response: str) -> Dict[str, Any]:
        ...


class MyelinOrchestrator:
    """
    Central orchestrator that coordinates all MYELIN pillars.
    Provides a unified interface for AI governance auditing.
    """
    
    def __init__(self):
        """Initialize all pillar modules"""
        self.fairness_module: FairnessModule = self._create_mock_fairness()
        self.factual_module: FactualModule = self._create_mock_factual()
        self.toxicity_module: ConversationAuditModule = self._create_mock_toxicity()
        self.governance_module: ConversationAuditModule = self._create_mock_governance()
        self.bias_module: ConversationAuditModule = self._create_mock_bias()
        self.factual_meta_rule: Optional[FactualMetaRule] = None
        
        self._initialize_modules()

    @staticmethod
    def _load_symbol(module_path: str, symbol_name: str) -> Any:
        """Load symbol dynamically to support pluggable module trees."""
        module = importlib.import_module(module_path)
        return getattr(module, symbol_name)
    
    def _initialize_modules(self):
        """Dynamically load all pillar modules with graceful error handling"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Store original sys.path to restore after each pillar
        original_path = sys.path.copy()
        
        # Fairness Pillar
        try:
            fairness_path = os.path.join(base_path, "Myelin_Fairness_Pillar_RICH_FINAL")
            sys.path.insert(0, fairness_path)
            FairnessEnsemble = self._load_symbol("ensemble", "FairnessEnsemble")
            self.fairness_module = FairnessEnsemble(os.path.join(fairness_path, "rules"))
            logger.info("✅ Fairness Pillar loaded")
        except Exception as e:
            logger.warning(f"⚠️  Fairness Pillar failed to load: {e}")
            self.fairness_module = self._create_mock_fairness()
            
        # Factual Check Pillar (FCAM)
        try:
            self._clear_module_namespace("modules")
            fcam_path = os.path.join(base_path, "FCAM_fixed", "FCAM_fixed", "Factual_Consistency_Accountability_Module")
            sys.path.insert(0, fcam_path)
            sys.path.insert(0, os.path.join(fcam_path, "modules"))
            
            rule_specs = [
                ("modules.factual.rules.rule_01_source_alignment", "SourceAlignmentRule"),
                ("modules.factual.rules.rule_02_atomic_claims", "AtomicClaimDecompositionRule"),
                ("modules.factual.rules.rule_03_claim_verification", "ClaimLevelVerificationRule"),
                ("modules.factual.rules.rule_04_qa_consistency", "QABasedConsistencyRule"),
                ("modules.factual.rules.rule_05_coverage", "CoverageCompletenessRule"),
                ("modules.factual.rules.rule_06_stability", "MetamorphicStabilityRule"),
                ("modules.factual.rules.rule_07_multilingual_consistency", "MultilingualConsistencyRule"),
                ("modules.factual.rules.rule_08_external_knowledge", "ExternalKnowledgeVerificationRule"),
                ("modules.factual.rules.rule_09_token_validation", "TokenValidationRule"),
                ("modules.factual.rules.rule_10_token_correction", "TokenCorrectionRule"),
                ("modules.factual.rules.rule_11_numerical_consistency", "NumericalConsistencyRule"),
                ("modules.factual.rules.rule_12_temporal_consistency", "TemporalConsistencyRule"),
                ("modules.factual.rules.rule_13_entity_consistency", "EntityConsistencyRule"),
                ("modules.factual.rules.rule_14_causal_consistency", "CausalConsistencyRule"),
                ("modules.factual.rules.rule_15_internal_consistency", "InternalConsistencyRule"),
                ("modules.factual.rules.rule_16_severity", "HallucinationSeverityRule"),
                ("modules.factual.rules.rule_17_uncertainty", "UncertaintySignalingRule"),
                ("modules.factual.rules.rule_18_cross_model", "CrossModelAgreementRule"),
                ("modules.factual.rules.rule_19_domain_sensitivity", "DomainSensitivityRule"),
            ]

            fcam_rules = [
                self._load_symbol(module_path, class_name)()
                for module_path, class_name in rule_specs
            ]

            FinalFactualConfidenceRule = self._load_symbol(
                "modules.factual.rules.rule_20_final_decision",
                "FinalFactualConfidenceRule",
            )
            FactualEnsembleManager = self._load_symbol("modules.factual.ensemble_manager", "FactualEnsembleManager")

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
            
            self._clear_module_namespace("modules")
            
            ToxicityEnsembleManager = self._load_symbol("modules.toxicity.ensemble_manager", "ToxicityEnsembleManager")
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
            
            self._clear_module_namespace("modules")
            
            GovernanceEnsembleManager = self._load_symbol("modules.governance.ensemble_manager", "GovernanceEnsembleManager")
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
            
            self._clear_module_namespace("modules")
            
            BiasEnsembleManager = self._load_symbol("modules.bias.ensemble_manager", "BiasEnsembleManager")
            self.bias_module = BiasEnsembleManager()
            logger.info("✅ Bias Pillar loaded")
        except Exception as e:
            logger.warning(f"⚠️  Bias Pillar failed to load: {e}")
            self.bias_module = self._create_mock_bias()
            
        logger.info("🎯 MYELIN orchestrator initialized!")

    def _clear_module_namespace(self, root_module: str):
        """Remove cached package modules so each pillar resolves from its own repo tree."""
        stale_modules = [
            module_name
            for module_name in list(sys.modules.keys())
            if module_name == root_module or module_name.startswith(f"{root_module}.")
        ]
        for module_name in stale_modules:
            del sys.modules[module_name]
    
    def _create_mock_fairness(self) -> FairnessModule:
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
    
    def _create_mock_factual(self) -> FactualModule:
        """Create mock factual module"""
        class MockFactual:
            def evaluate(self, model_output, source_text=None):
                return 0.5, {"note": "Factual pillar not available - install dependencies"}
        return MockFactual()
    
    def _create_mock_toxicity(self) -> ConversationAuditModule:
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
    
    def _create_mock_governance(self) -> ConversationAuditModule:
        """Create mock governance module"""
        class MockGovernance:
            def run_full_audit(self, user_input, bot_response):
                return {
                    "governance_risk_score": 0.0,
                    "details": [],
                    "note": "Governance pillar not available - install dependencies"
                }
        return MockGovernance()
    
    def _create_mock_bias(self) -> ConversationAuditModule:
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
        minimum_decision = "ALLOW"

        decision_rank = {
            "ALLOW": 0,
            "REVIEW": 1,
            "WARN": 2,
            "BLOCK": 3,
        }

        def _raise_minimum_decision(target_decision: str):
            nonlocal minimum_decision
            current_rank = decision_rank.get(minimum_decision, 0)
            target_rank = decision_rank.get(target_decision, 0)
            if target_rank > current_rank:
                minimum_decision = target_decision
        
        if toxicity_result["status"] == "success":
            tox_score = toxicity_result["report"].get("toxicity_score", 0)
            risk_score += tox_score * 0.35  # 35% weight
            tox_decision = toxicity_result["report"].get("decision", "ALLOW")

            # Prevent unsafe downgrades when toxicity engine already escalated.
            if tox_decision == "ALLOW_WITH_CAUTION":
                _raise_minimum_decision("REVIEW")
            elif tox_decision in decision_rank:
                _raise_minimum_decision(tox_decision)

            if tox_score > 0.5:
                risk_factors.append(f"High toxicity detected ({tox_score})")
        
        if governance_result["status"] == "success":
            gov_score = governance_result["report"].get("governance_risk_score", 0)
            risk_score += gov_score * 0.25  # 25% weight
            if gov_score > 0.5:
                risk_factors.append(f"Governance violations ({gov_score})")
        
        if bias_result["status"] == "success":
            bias_score = bias_result["report"].get(
                "bias_score",
                bias_result["report"].get("global_bias_index", 0),
            )
            risk_score += bias_score * 0.20  # 20% weight
            if bias_score > 0.5:
                risk_factors.append(f"Bias detected ({bias_score})")
        
        if factual_result["status"] == "success":
            fact_score = 1 - factual_result.get("final_score", 1.0)  # Invert (lower is worse)
            risk_score += fact_score * 0.20  # 20% weight
            if fact_score > 0.5:
                risk_factors.append(f"Low factual accuracy ({factual_result.get('final_score', 0)})")
        else:
            _raise_minimum_decision("REVIEW")
            risk_factors.append("Factual engine failed; manual review required")
        
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

        # Enforce minimum escalation derived from pillar-level outcomes.
        if decision_rank.get(minimum_decision, 0) > decision_rank.get(decision, 0):
            decision = minimum_decision
            if decision == "BLOCK":
                risk_level = "CRITICAL"
            elif decision == "WARN":
                risk_level = "HIGH"
            elif decision == "REVIEW":
                risk_level = "MEDIUM"
            else:
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
_orchestrator_instance: Optional[MyelinOrchestrator] = None

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
