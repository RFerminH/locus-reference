from shared import StructuredInput
from session_record import start_session, record


def run_structured(client, session):
    while True:
        data = input("Enter the evidence: ").strip()
        if data:
            break
        print("Evidence is required.")
    record(session, "human_input", "evidence_entered", text=data)

    while True:
        inferences = input("Enter your formulation: ").strip()
        if inferences:
            break
        print("Your formulation is required.")
    record(session, "human_input", "formulation_entered", text=inferences)

    return StructuredInput(evidence_packet=data, potestas_formulation=inferences)


if __name__ == "__main__":
    print(run_structured(None, start_session()))