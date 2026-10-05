from shared import DiagnosticVector, FormulationAnalysis, UnsupportedClaim, EvidentiaryAnalysis
from analysis_display import render_analysis

shown = DiagnosticVector(finding="night sweats", case_state="present", presence_frequency_given_formulation="usually_present", case_effect="supports", assessment_basis="Compatible with the formulation.", evidence_basis="night sweats")
aside = DiagnosticVector(finding="dizziness", case_state="not_identified", presence_frequency_given_formulation="rarely_present", case_effect="unresolved", assessment_basis="Not documented.", evidence_basis="")
neutral = DiagnosticVector(finding="fever", case_state="absent", presence_frequency_given_formulation="rarely_present", case_effect="neutral", assessment_basis="Does not alter the formulation.", evidence_basis="no fever")

a = FormulationAnalysis(formulation="X", mapped_clinical_node="x", stated_qualifiers=[], vectors=[shown, aside])
b = FormulationAnalysis(formulation="Y", mapped_clinical_node="y", stated_qualifiers=["q"], vectors=[neutral])
claim = UnsupportedClaim(source="potestas", claim="there is no pain", note="Not stated in the evidence.")

analysis = EvidentiaryAnalysis(
    decision_fork="Example fork.",
    potestas_formulation_analysis=a,
    potentia_formulation_analysis=b,
    shared_ground=["Example shared point."],
    key_discriminators=[],
    missing_discriminating_evidence=["Example missing item."],
    unsupported_or_overextended_claims=[claim],
    unresolved_uncertainties=["Example uncertainty."],
)

print(render_analysis(analysis))