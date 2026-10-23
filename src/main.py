import os
from dotenv import load_dotenv
from google import genai
from intake_partition import run_intake
from structured_input import run_structured
from break_glass import run_break_glass
from clinical_pipeline import run_pipeline
from session_record import start_session, record

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

LEGEND = (
    "\nLOCUS: clinical second opinion\n"
    "  Potestas:     You, the clinician. You formulate and decide.\n"
    "  Potentia:     The AI support, split into separate components. Each does one task\n"
    "                and receives only the information that task needs.\n"
    "  Break-Glass:  Urgent access to Potentia's response, with no formulation or explanation required first.\n"
    "\n"
    "  Evidence:     What was observed or reported: symptoms, history, test results.\n"
    "  Formulation:  Your diagnostic label or hypothesis, based on that evidence.\n"
    "\nYou explain your own judgment before you see Potentia's reasoning. This step is deliberate:\n"
    "your reasoning is written down and recorded before that exposure. When asked to explain, type 'skip'\n"
    "to see what Potentia is withholding at once, or 'no' (or just press Enter) to finish without it.\n"
    "Break-Glass (option 3, or when urgency is flagged) is the urgent route. All these choices are recorded.\n"
    "\nUsual sequence:\n"
    "  1. Potestas, case entry: enter the evidence and your formulation.\n"
    "     Free text is split by Potentia [Intake Splitter] for your review.\n"
    "  2. Potentia [Urgency Screener]: checks the evidence for urgency. If urgency is flagged,\n"
    "     the sequence stops and you choose whether to use Break-Glass.\n"
    "  3. Potestas, confirmation: confirm your formulation. This version is kept for comparison;\n"
    "     you can revise it at the end.\n"
    "  4. Potentia [Formulator]: proposes one leading formulation and a differential from the evidence alone,\n"
    "     without seeing yours. The differential is shown with its reasoning.\n"
    "  5. Potentia [Comparator]: compares the two formulations: match, partial match or divergence.\n"
    "     A match shows Potentia's formulation here.\n"
    "  6. Potestas, explanation: what supports your formulation, what would weaken or refute it,\n"
    "     and what is uncertain or missing.\n"
    "  7. Potentia [Analyst]: compares both formulations and their reasoning against the evidence,\n"
    "     after the Formulator's reasoning is shown. Depends on your choices and availability.\n"
    "  8. Potestas, final decision: keep, revise or defer your formulation.\n"
)


def run_cognitive_contract(session):

    print(LEGEND)
    entry_mode = input(
        "Choose how to enter the case:\n"
        "  1  Free text (evidence and formulation together)\n"
        "  2  Separate fields (evidence, then formulation)\n"
        "  3  Break-Glass (urgent)\n"
        "> "
    ).strip()
    record(session, "human_input", "entry_mode_selected", mode=entry_mode)

    if entry_mode == "1":
        case_input = run_intake(client, session)
    elif entry_mode == "2":
        case_input = run_structured(client, session)
    elif entry_mode == "3":
        return run_break_glass(client, session)
        
    else:
        print("Invalid choice. Session closed.")
        return "cancelled"

    if case_input is None:
        saved = record(session, "runtime", "intake_unavailable")
        print("Could not process your text.")
        if saved:
            print("Your text is saved in " + session["path"])
        else:
            print("Your text could not be saved. Copy it before closing this window.")
        return "failed"

    return run_pipeline(case_input, client, session)


def main():
    session = start_session()
    try:
        outcome = run_cognitive_contract(session)
    except KeyboardInterrupt:
        record(session,"runtime","session_ended", outcome="interrupted")
        print("\nSession interrupted.")

    except Exception as error:
        record(session, "runtime","session_ended", outcome="failed", error=repr(error))
        raise
    else:
        record(session, "runtime", "session_ended", outcome=outcome)

if __name__ == "__main__":
    main()