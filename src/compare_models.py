from dotenv import load_dotenv
from google import genai
from google.genai import types
from shared import PotestasResponse, PotentiaResponse, RationaleStage
from evidentiary_potentia import get_evidentiary_analysis

MODEL = "gemini-3.6-flash"
THINKING = types.ThinkingLevel.HIGH
RUNS = 5

load_dotenv()
client = genai.Client()

EVIDENCE = "Protruding bump at the umbilicus, more noticeable after physical effort or coughing, no pain, no discoloration, reducible on gentle pressure."

POTESTAS = PotestasResponse(
    potestas_formulation="Umbilical lipoma",
    rationale="A painless lump at the umbilicus could be a lipoma. What would weaken it is that it enlarges with coughing and reduces under pressure, which a fatty tumor would not do. What remains uncertain is the consistency and the presence of a palpable fascial defect, which were not described.",
    rationale_stage=RationaleStage.PRE_EXPOSURE,
)

POTENTIA = PotentiaResponse(
    potentia_formulation="Uncomplicated umbilical hernia.",
    rationale="Supporting evidence: The clinical presentation of a soft protruding mass at the umbilicus that becomes more prominent with increased intra-abdominal pressure (physical effort, coughing) and is easily reducible without pain or discoloration strongly aligns with an uncomplicated umbilical hernia. Refuting/Weakening factors: Development of severe pain, local discoloration (erythema or dark discoloration), irreducibility, or associated systemic features like nausea and vomiting would refute this uncomplicated formulation and indicate strangulation, incarceration, or an alternative non-hernial mass (such as an umbilical granuloma, lipoma, or Sister Mary Joseph nodule). Uncertainties/Missing information: The size of the underlying fascial defect, duration of the swelling, risk factors (e.g., ascites, obesity, multiparity), abdominal exam details, and diagnostic ultrasound findings are not provided.",
)

PREFIXES = ["absence of", "lack of", "no ", "without "]


def summarize(analysis):
    polarity = 0
    suspicious = 0
    for name, block in (("POTESTAS", analysis.potestas_formulation_analysis), ("POTENTIA", analysis.potentia_formulation_analysis)):
        for v in block.vectors:
            print("  " + name + " | " + v.finding + " | " + v.case_state.value + " | " + v.presence_frequency_given_formulation.value + " | " + v.case_effect.value)
            for prefix in PREFIXES:
                if v.finding.lower().startswith(prefix):
                    polarity = polarity + 1
            if v.case_state.value == "absent" and v.presence_frequency_given_formulation.value == "high" and v.case_effect.value == "supports":
                suspicious = suspicious + 1
    claims = len(analysis.unsupported_or_overextended_claims)
    print("  SUMMARY: polarity violations = " + str(polarity) + ", absent/high/supports rows = " + str(suspicious) + ", unsupported claims = " + str(claims))


for run in range(1, RUNS + 1):
    print("\n=== " + MODEL + " | thinking " + str(THINKING) + " | run " + str(run) + " ===")
    analysis = get_evidentiary_analysis(EVIDENCE, POTESTAS, POTENTIA, client, MODEL, THINKING)
    if analysis is None:
        print("  no result")
    else:
        summarize(analysis)