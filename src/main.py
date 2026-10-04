import os
from dotenv import load_dotenv
from google import genai
from intake_partition import run_intake
from structured_input import run_structured
from break_glass import run_break_glass
from clinical_pipeline import run_pipeline

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def run_cognitive_contract():
    entry_mode = input("Select entry mode.\nIntake Partition Input.(1) Natural text input.\nStructured Input.(2) Evidentiary data and formulation segregated.\nBREAK GLASS.(3) Urgency mode bypassing pairing protocol.: ")

    if entry_mode == "1":
        case_input = run_intake(client)
    elif entry_mode == "2":
        case_input = run_structured(client)
    elif entry_mode == "3":
        run_break_glass(client)
        return
    else:
        print("Invalid selection")
        return

    if case_input is None:
        print("Unable to complete intake.")
        return

    run_pipeline(case_input, client)


if __name__ == "__main__":
    run_cognitive_contract()