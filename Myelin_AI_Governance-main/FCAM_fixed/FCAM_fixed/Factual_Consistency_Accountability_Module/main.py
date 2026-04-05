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

# Example model output and source
model_output = (
    "The policy provides coverage for 12 months "
    "and may include hospitalization benefits."
)

source_text = (
    "The policy provides coverage for 6 months "
    "and includes hospitalization benefits."
)

# Load all 19 scoring rules (Rule 20 is meta)
rules = [
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

manager = FactualEnsembleManager(rules)

final_score, report = manager.evaluate(
    model_output=model_output,
    source_text=source_text
)

# Meta Rule (Rule 20)
final_rule = FinalFactualConfidenceRule()
meta_score, meta_report = final_rule.evaluate(
    model_output=model_output,
    source_text=source_text,
    final_score=final_score
)

# Print Report
print("\nFINAL FACTUAL SCORE:", round(final_score, 3))
print("\nDETAILED REPORT:")

for rule, info in report.items():
    print(f"\n{rule}")
    print(info)

print("\nMETA DECISION (Rule 20):")
print(meta_report)
