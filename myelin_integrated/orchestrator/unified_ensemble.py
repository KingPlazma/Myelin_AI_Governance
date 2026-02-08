"""
UNIFIED ENSEMBLE MANAGER
Manages the loading and execution of all 5 MYELIN pillars.
"""
import sys
import os
import logging
import importlib

# Configure logging to be silent unless it's an error
logging.basicConfig(level=logging.ERROR)

class UnifiedEnsembleManager:
    def __init__(self):
        self.pillars = {}
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.load_all_pillars()

    def load_all_pillars(self):
        print(">>> 🔄 Initializing MYELIN System (Loading 5 Pillars)...")
        
        # 1. Fairness Pillar
        try:
            path = os.path.join(self.base_path, "Myelin_Fairness_Pillar_RICH_FINAL")
            if path not in sys.path: sys.path.insert(0, path)
            from ensemble import FairnessEnsemble
            self.pillars['fairness'] = FairnessEnsemble(os.path.join(path, "rules"))
            print("  ✅ Fairness Pillar: ONLINE")
        except Exception as e:
            print(f"  ❌ Fairness Pillar: FAILED ({e})")

        # 2. Toxicity Pillar
        try:
            path = os.path.join(self.base_path, "Toxicity", "Toxicity")
            if path not in sys.path: sys.path.insert(0, path)
            from modules.toxicity.ensemble_manager import ToxicityEnsembleManager
            self.pillars['toxicity'] = ToxicityEnsembleManager()
            print("  ✅ Toxicity Pillar: ONLINE")
        except Exception as e:
            print(f"  ❌ Toxicity Pillar: FAILED ({e})")

        # 3. Governance Pillar
        try:
            gov_path = os.path.join(self.base_path, "Governance_Project", "Governance_Project")
            original_dir = os.getcwd()
            os.chdir(gov_path)
            if gov_path not in sys.path: sys.path.insert(0, gov_path)
            if 'modules' in sys.modules: del sys.modules['modules']
            from modules.governance.ensemble_manager import GovernanceEnsembleManager
            self.pillars['governance'] = GovernanceEnsembleManager()
            os.chdir(original_dir)
            print("  ✅ Governance Pillar: ONLINE")
        except Exception as e:
            print(f"  ❌ Governance Pillar: FAILED ({e})")
            try: os.chdir(original_dir)
            except: pass

        # 4. Bias Pillar
        try:
            bias_path = os.path.join(self.base_path, "BIAS", "mylin")
            original_dir = os.getcwd()
            os.chdir(bias_path)
            if bias_path not in sys.path: sys.path.insert(0, bias_path)
            if 'modules' in sys.modules: del sys.modules['modules']
            from modules.bias.ensemble_manager import BiasEnsembleManager
            self.pillars['bias'] = BiasEnsembleManager()
            os.chdir(original_dir)
            print("  ✅ Bias Pillar: ONLINE")
        except Exception as e:
            print(f"  ❌ Bias Pillar: FAILED ({e})")
            try: os.chdir(original_dir)
            except: pass

        # 5. Factual Pillar (FCAM) - NOW ONLINE!
        try:
            fcam_path = os.path.join(self.base_path, "FCAM_fixed", "FCAM_fixed", "Factual_Consistency_Accountability_Module")
            
            # Add path
            if fcam_path not in sys.path: sys.path.insert(0, fcam_path)
            
            # Clear conflicts
            if 'modules' in sys.modules: del sys.modules['modules']
            
            # Import Manager
            from modules.factual.ensemble_manager import FactualEnsembleManager
            
            # Import Rules (Lite Versions)
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

            # Initialize Rules
            rules = [
                SourceAlignmentRule(), AtomicClaimDecompositionRule(), ClaimLevelVerificationRule(),
                QABasedConsistencyRule(), CoverageCompletenessRule(), MetamorphicStabilityRule(),
                MultilingualConsistencyRule(), ExternalKnowledgeVerificationRule(), TokenValidationRule(),
                TokenCorrectionRule(), NumericalConsistencyRule(), TemporalConsistencyRule(),
                EntityConsistencyRule(), CausalConsistencyRule(), InternalConsistencyRule(),
                HallucinationSeverityRule(), UncertaintySignalingRule(), CrossModelAgreementRule(),
                DomainSensitivityRule(), FinalFactualConfidenceRule()
            ]
            
            self.pillars['factual'] = FactualEnsembleManager(rules)
            print("  ✅ Factual Pillar: ONLINE (Lite Mode)")
            
        except Exception as e:
            print(f"  ❌ Factual Pillar: FAILED ({e})")

    def run_audit(self, user_input, bot_response, source_text=None):
        results = {}
        
        # Toxicity
        if 'toxicity' in self.pillars:
            results['toxicity'] = self.pillars['toxicity'].run_full_audit(user_input, bot_response)
            
        # Governance
        if 'governance' in self.pillars:
            results['governance'] = self.pillars['governance'].run_full_audit(user_input, bot_response)
            
        # Bias
        if 'bias' in self.pillars:
            results['bias'] = self.pillars['bias'].run_full_audit(user_input, bot_response)
            
        # Factual
        if 'factual' in self.pillars and source_text:
            score, report = self.pillars['factual'].evaluate(bot_response, source_text)
            results['factual'] = {
                "score": score,
                "report": report,
                "violation": score < 0.7  # Threshold for violation
            }
            
        return results
