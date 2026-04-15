
import re
import sys
import os
import logging
import importlib

# Configure logging to be silent unless it's an error
logging.basicConfig(level=logging.ERROR)

class UnifiedEnsembleManager:
    def __init__(self):
        self.pillars = {}
        # Fairness Buffer: Stores (y_true, y_pred, sensitive) tuples
        self.fairness_buffer = {
            "y_true": [],
            "y_pred": [],
            "sensitive": []
        }
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.load_all_pillars()

    def _clear_module_namespace(self, root_module):
        """Clear cached package modules so each pillar resolves its own module tree."""
        stale_modules = [
            module_name
            for module_name in list(sys.modules.keys())
            if module_name == root_module or module_name.startswith(f"{root_module}.")
        ]
        for module_name in stale_modules:
            del sys.modules[module_name]

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
            self._clear_module_namespace("modules")
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
            self._clear_module_namespace("modules")
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
            self._clear_module_namespace("modules")
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
            self._clear_module_namespace("modules")
            
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

    def _update_fairness_buffer(self, user_input, outcome_score):
        """
        Dynamically updates fairness statistics based on user input patterns.
        """
        # 1. Detect Sensitive Attribute (Heuristic for Gender)
        # 0 = Male, 1 = Female, None = Unknown
        sensitive_val = None
        
        # Male-coded tokens
        if re.search(r'\b(man|men|male|boy|he|him|his)\b', user_input, re.IGNORECASE):
            sensitive_val = 0
        # Female-coded tokens
        elif re.search(r'\b(woman|women|female|girl|she|her)\b', user_input, re.IGNORECASE):
            sensitive_val = 1
            
        # Only track if we have a detected group
        if sensitive_val is not None:
            # 2. Determine Outcome (y_pred)
            # system is Safe (score low), y_pred should be 1.
            # system is Toxic (score high), y_pred should be 0.
            y_pred_val = 1 if outcome_score < 0.5 else 0
            
            # 3. Ground Truth (y_true)
            # We assume the system SHOULD always be favorable/safe (1).
            y_true_val = 1
            
            self.fairness_buffer['sensitive'].append(sensitive_val)
            self.fairness_buffer['y_pred'].append(y_pred_val)
            self.fairness_buffer['y_true'].append(y_true_val)

    def run_audit(self, user_input, bot_response, source_text=None):
        results = {}
        
        # 1. Toxicity
        tox_score = 0.0
        if 'toxicity' in self.pillars:
            try:
                res = self.pillars['toxicity'].run_full_audit(user_input, bot_response)
                results['toxicity'] = res
                # "score" in toxicity usually means probability of toxicity
                if res.get('risk_level') == 'HIGH': tox_score = 1.0
            except:
                results['toxicity'] = {"error": "Toxicity Exec Failed"}
            
        # 2. Governance
        if 'governance' in self.pillars:
            results['governance'] = self.pillars['governance'].run_full_audit(user_input, bot_response)
            
        # 3. Bias
        if 'bias' in self.pillars:
            results['bias'] = self.pillars['bias'].run_full_audit(user_input, bot_response)

        # 4. Fairness (Dynamic Accumulation)
        # Update buffer with this transaction
        self._update_fairness_buffer(user_input, tox_score)
        
        if 'fairness' in self.pillars:
            # Try to run fairness audit on accumulated data
            # Only run if we have enough samples (e.g. at least 2 per group)
            s_counts = {0: 0, 1: 0}
            for s in self.fairness_buffer['sensitive']:
                s_counts[s] = s_counts.get(s, 0) + 1
            
            if s_counts[0] >= 5 and s_counts[1] >= 5:
                # We have enough data for a "Live Fairness Check" (Lite Thresholds)
                f_res = self.pillars['fairness'].run(
                    self.fairness_buffer['y_true'], 
                    self.fairness_buffer['y_pred'], 
                    self.fairness_buffer['sensitive']
                )
                results['fairness'] = f_res
            else:
                results['fairness'] = {
                    "status": "ACCUMULATING_DATA", 
                    "msg": f"Collecting live samples. Current: {s_counts}"
                }

        # 5. Factual
        if 'factual' in self.pillars and source_text:
            try:
                score, report = self.pillars['factual'].evaluate(bot_response, source_text)
                results['factual'] = {
                    "score": score,
                    "report": report,
                    "violation": score < 1.0  # Stricter Threshold to catch hallucinations
                }
            except Exception as e:
                results['factual'] = {"error": str(e), "violation": True}
            
        return results

    def run_fairness_audit(self, y_true, y_pred, sensitive):
        """
        Runs the Fairness Pillar for batch datasets.
        """
        if 'fairness' in self.pillars:
            return self.pillars['fairness'].run(y_true, y_pred, sensitive)
        return {"error": "Fairness pillar not loaded"}
