from shared import StructuredInput
from session_record import start_session, record


def run_structured(client, session):
    while True:
        data = input("Enter evidentiary data: ").strip()
        if data:
            break
        print("Evidentiary data required to proceed.")
    record(session, "evidence_entered", text=data)

    while True:
        inferences = input("Enter potestas (your) formulation: ").strip()
        if inferences:
            break
        print("Potestas formulation required to proceed.")
    record(session, "formulation_entered", text=inferences)

    return StructuredInput(evidence_packet=data, potestas_formulation=inferences)


if __name__ == "__main__":
    print(run_structured(None, start_session()))