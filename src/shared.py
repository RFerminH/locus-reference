from pydantic import BaseModel, Field, model_validator
from enum import Enum


AFFIRMATIVE_RESPONSES = ["yes", "y", "ye", "yea", "yeah", "yep", "yup", "aye", "ok", "okay", "k", "sure", "correct", "confirm", "confirmed", "affirmative"]


def ask_confirmation(formulation):
    return input(f"\nConfirm your formulation: '{formulation}' (y/n): ")


def ask_required(question):
    answer=""
    while not answer:
        answer=input(question).strip()
    return answer


STEP_LABELS = {
    "run_safety_screening": ("Potentia [Urgency Screener]", "checking the evidence for urgency"),
    "get_potentia_response": ("Potentia [Formulator]", "proposing its own formulation from the evidence"),
    "match_formulations": ("Potentia [Comparator]", "comparing the two formulations"),
    "get_evidentiary_analysis": ("Potentia [Analyst]", "preparing the comparative analysis"),
}


def call_with_standby(func, *args):
    component, action = STEP_LABELS.get(
        func.__name__, 
        (func.__name__, "working")
        )
    result = None
    while result is None:
        print(f"\n{component} is {action}...")
        result = func(*args)
        if result is None:
            retry = input(f"\n{component} failed after three attempts. Retry? (y/n): ").strip().lower()
            if retry not in AFFIRMATIVE_RESPONSES:
                return None
    return result



class IntakePartition(BaseModel):
    evidence_packet: str = Field(description="Case evidence: symptoms, temporalities, antecedents, facts.")
    potestas_formulation: str = Field(description="Subjective inferences focused in the Diagnostic and predictions.")

class StructuredInput(BaseModel):
    evidence_packet: str = Field(description="Case evidence: symptoms, temporalities, antecedents, facts.")
    potestas_formulation: str = Field(description="Subjective inferences focused in the Diagnostic and predictions.")

class PotentiaResponse(BaseModel):
    potentia_formulation: str = Field(description="One leading diagnostic formulation derived from the case evidence: a single condition or hypothesis, not a list of alternatives. If the evidence is insufficient for a leading formulation, state that here.")
    rationale: str = Field(description="Inspectable justification addressing what in the evidence supports the leading formulation, what would refute or weaken it, and what remains uncertain or missing.")
    differential: list[str] = Field(description="Other formulations still worth considering, most plausible first, one per item. Empty list when none.")


class MatchingResult(str, Enum):
    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    DIVERGENCE = "divergence"

class MatchingOutcome(BaseModel):
    result: MatchingResult = Field(description="Diagnostic matching relationship between the two formulations.")


class SafetyScreeningResult(str, Enum):
    NONE = "none"
    URGENT_RETURN = "urgent_return"

class SafetyScreening(BaseModel):
    result: SafetyScreeningResult = Field(description="Whether the supplied evidence activates the reserved urgent-return condition.")


class RationaleStage(str, Enum):
    PRE_EXPOSURE = "pre_exposure"
    POST_CONVERGENCE_PRE_RATIONALE_EXPOSURE = "post_convergence_pre_rationale_exposure"
    POST_POTENTIA_RATIONALE_EXPOSURE = "post_potentia_rationale_exposure"

class PotestasResponse(BaseModel):
    potestas_formulation: str = Field(description="The clinician's sealed formulation, unchanged.")
    rationale: str = Field(description="The clinician's own account of what supports this formulation, what would refute or weaken it, and what remains uncertain or missing.")
    rationale_stage: RationaleStage = Field(description="Whether this rationale was produced before any exocortical exposure, after convergence was known but before Potentia's rationale was seen, or after Potentia's rationale was seen.")


class CaseObservationState(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    NOT_IDENTIFIED = "not_identified"

class PresenceFrequency(str, Enum):
    USUALLY_PRESENT = "usually_present"
    SOMETIMES_PRESENT = "sometimes_present"
    RARELY_PRESENT = "rarely_present"
    UNKNOWN = "unknown"

class CaseEffect(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    NEUTRAL = "neutral"
    UNRESOLVED = "unresolved"

class DiagnosticVector(BaseModel):
    finding: str = Field(description="The clinical phenomenon being evaluated, named independently of its observed state, for example 'dizziness' or 'night sweats'. Represent documented presence, absence, or uncertainty only in case_state. For a composite pattern, state its constituents and required relationships in assessment_basis.")
    case_state: CaseObservationState = Field(description="Whether the finding is present, explicitly absent, or not identified in the supplied evidence.")
    presence_frequency_given_formulation: PresenceFrequency = Field(description="How commonly the named clinical phenomenon is present in cases of the formulation as supplied, given the documented context and clinical phase. USUALLY_PRESENT means present in most cases, SOMETIMES_PRESENT means present in some cases, RARELY_PRESENT means present in few cases, and UNKNOWN means the available knowledge or context does not support a judgment. Evaluate the presence of the named phenomenon independently of case_state.")    
    case_effect: CaseEffect = Field(description="Whether the finding's documented case state supports, weakens, is neutral toward, or leaves unresolved the formulation as supplied, at its stated level of specificity. A not_identified finding must not be treated as absent.")
    assessment_basis: str = Field(description="One or two sentences explaining why the finding has the assigned presence frequency and case effect. Describe the finding's graded evidentiary contribution and its relevant limitation, using directional wording such as points toward, is compatible with, or reduces concern for; a clinical sign does not settle a diagnosis, complication, or mechanism by itself. Leave broader diagnostic conclusions to the clinician (Potestas).")
    evidence_basis: str = Field(description="Exact supporting span or source reference from the supplied case. Required for present and absent; empty only for not_identified.")

    @model_validator(mode="after")
    def validate_evidence_basis(self):
        evidence = self.evidence_basis.strip()

        if self.case_state is CaseObservationState.NOT_IDENTIFIED and evidence:
            raise ValueError("evidence_basis must be empty when case_state is not_identified")

        if self.case_state in {CaseObservationState.PRESENT, CaseObservationState.ABSENT} and not evidence:
            raise ValueError("evidence_basis is required when case_state is present or absent")

        return self


class FormulationAnalysis(BaseModel):
    formulation: str = Field(description="The sealed formulation exactly as supplied.")
    mapped_clinical_node: str = Field(description="The clinical entity identified by the formulation. When both formulations identify the same entity, use the same normalized label.")
    stated_qualifiers: list[str] = Field(description="Only qualifiers explicitly stated in the formulation, such as subtype, severity, complication status, laterality, or temporal state. Empty when none are stated.")
    vectors: list[DiagnosticVector] = Field(description="Findings evaluated against the formulation exactly as supplied and at its stated level of specificity.")


class ClaimSource(str, Enum):
    POTESTAS = "potestas"
    POTENTIA = "potentia"


class UnsupportedClaim(BaseModel):
    source: ClaimSource = Field(description="Which party's rationale made this claim.")
    claim: str = Field(description="The claim, as stated.")
    note: str = Field(description="Why this claim is not established by the supplied evidence.")


class EvidentiaryAnalysis(BaseModel):
    decision_fork: str = Field(description="Single-sentence summary of where the two formulations converge and where they diverge.")
    potestas_formulation_analysis: FormulationAnalysis = Field(description="Evidentiary analysis of the formulation authored by Potestas.")
    potentia_formulation_analysis: FormulationAnalysis = Field(description="Evidentiary analysis of the formulation authored independently by Potentia.")
    shared_ground: list[str] = Field(description="Interpretive propositions about the case that both formulations share (for example chronicity, organ system involved, or a common mechanism), beyond citing the same findings. Do not restate findings already evaluated in both analyses. Include only propositions that both analyses actually support; do not invent a common mechanism to fill the field. Empty list when the only overlap is shared findings.")
    key_discriminators: list[str] = Field(description="Evidence that materially explains, supports, challenges, or could resolve the decision_fork between the supplied formulations, including evidence bearing on a qualifier stated by only one formulation. It may overlap with shared_ground. Empty only when no evidence materially bears on the difference.")
    missing_discriminating_evidence: list[str] = Field(description="Evidence not supplied that would materially help resolve the decision_fork between the formulations. Exclude general characterization, background risk factors, prognosis, and management information that would not change that comparison. Empty list when none.")
    unsupported_or_overextended_claims: list[UnsupportedClaim] = Field(description="Claims in either rationale that are not established by the supplied evidence.")
    unresolved_uncertainties: list[str] = Field(description="Uncertainties that remain after the analysis and materially affect the decision_fork between the formulations. Do not carry over an uncertainty from either rationale solely because its author mentioned it. Empty list when none.")