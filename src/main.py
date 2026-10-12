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


def run_cognitive_contract(session):

    entry_mode = input("Select entry mode.\nIntake Partition Input.(1) Natural text input.\nStructured Input.(2) Evidentiary data and formulation segregated.\nBREAK GLASS.(3) Urgency mode bypassing pairing protocol.: ")
    record(session, "human_input", "entry_mode_selected", mode=entry_mode)

    if entry_mode == "1":
        case_input = run_intake(client, session)
    elif entry_mode == "2":
        case_input = run_structured(client, session)
    elif entry_mode == "3":
        return run_break_glass(client, session)
        
    else:
        print("Invalid selection")
        return "cancelled"

    if case_input is None:
        saved = record(session, "runtime", "intake_unavailable")
        print("Unable to complete intake.")
        if saved:
            print("Your input is saved in " + session["path"])
        else:
            print("Your input could not be saved. Copy it before closing this window.")
        return "failed"

    run_pipeline(case_input, client, session)
    return "completed"


def main():
    session = start_session()
    try:
        outcome = run_cognitive_contract(session)
    except KeyboardInterrupt:
        record(session,"runtime","session_ended", outcome="interrupted")
        print("\nSession interrupted by user.")

    except Exception as error:
        record(session, "runtime","session_ended", outcome="failed", error=repr(error))
        raise
    else:
        record(session, "runtime", "session_ended", outcome=outcome)

if __name__ == "__main__":
    main()