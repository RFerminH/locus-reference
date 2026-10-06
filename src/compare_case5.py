from dotenv import load_dotenv
from google import genai
from google.genai import types
from shared import PotestasResponse, PotentiaResponse, RationaleStage
from evidentiary_potentia import get_evidentiary_analysis

MODEL = "gemini-3.6-flash"
THINKING = None
RUNS = 5

load_dotenv()
client = genai.Client()

EVIDENCE = "Child, 6 years old, with fever and fatigue since yesterday, no rash yet. A classmate was diagnosed with chickenpox ten days ago."

POTESTAS = PotestasResponse(
    potestas_formulation="Chickenpox",
    rationale="The contact ten days ago and the fever fit the early phase of chickenpox. What would weaken it is a rash with another pattern, or an immunization history I do not know. What remains uncertain is whether the rash will appear in the next days.",
    rationale_stage=RationaleStage.POST_CONVERGENCE_PRE_RATIONALE_EXPOSURE,
)

POTENTIA = PotentiaResponse(
    potentia_formulation="Suspected early varicella (chickenpox) prodrome in a 6-year-old child.",
    rationale="Supporting evidence includes known exposure to a confirmed classmate with chickenpox 10 days prior, which precisely matches the lower bound of the typical 10 to 21 day varicella incubation period. Additionally, acute onset of fever and fatigue 1 day ago is characteristic of the 24-to-48-hour viral prodrome that precedes the exanthem. Refuting or weakening factors include the current absence of the pathognomonic pruritic maculopapular or vesicular rash, meaning the presentation is currently non-specific and could represent another acute pediatric viral illness. Uncertainties include the child's varicella vaccination history, whether any early mucosal or hidden skin lesions are present, and whether the characteristic rash will emerge over the next 24 to 48 hours.",
)

PREFIXES = ["absence of", "lack of", "no ", "without "]


def summarize(analysis):
    polarity = 0
    rash_weakens = 0
    for name, block in (("POTESTAS", analysis.potestas_formulation_analysis), ("POTENTIA", analysis.potentia_formulation_analysis)):
        for v in block.vectors:
            print("  " + name + " | " + v.finding + " | " + v.case_state.value + " | " + v.presence_frequency_given_formulation.value + " | " + v.case_effect.value)
            if v.case_state.value == "absent":
                print("      basis: " + v.assessment_basis)
            for prefix in PREFIXES:
                if v.finding.lower().startswith(prefix):
                    polarity = polarity + 1
            if "rash" in v.finding.lower() and v.case_effect.value == "weakens":
                rash_weakens = rash_weakens + 1
                print("      >>> RASH ROW WEAKENS")
    for claim in analysis.unsupported_or_overextended_claims:
        print("  CLAIM [" + claim.source.value + "]: " + claim.claim)
    claims = len(analysis.unsupported_or_overextended_claims)
    print("  SUMMARY: polarity violations = " + str(polarity) + ", rash rows weakening = " + str(rash_weakens) + ", unsupported claims = " + str(claims))


for run in range(1, RUNS + 1):
    print("\n=== CASE 5 | " + MODEL + " | thinking " + str(THINKING) + " | run " + str(run) + " ===")
    analysis = get_evidentiary_analysis(EVIDENCE, POTESTAS, POTENTIA, client, MODEL, THINKING)
    if analysis is None:
        print("  no result")
    else:
        summarize(analysis)