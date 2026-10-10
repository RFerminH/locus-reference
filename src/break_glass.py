from evidentiary_return import get_potentia_response
from session_record import record


def run_break_glass(client, session):
    print("Break-Glass invoked. Ordinary Pairing Hold sequence bypassed by explicit Potestas decision.")
    record(session, "human_input", "break_glass_invoked", route="direct")

    raw_evidence = input("Enter case evidence: ").strip()
    if not raw_evidence:
        print("No evidence supplied. Nothing to evaluate.")
        record(session,"runtime", "break_glass_closed", reason="no_evidence")
        return
    record(session, "human_input", "evidence_entered", text=raw_evidence)

    potentia_response = get_potentia_response(raw_evidence, client)

    if potentia_response is None:
        record(session, "runtime", "potentia_response_unavailable")
        print("Unable to obtain Potentia's independent clinical support. Proceed with clinical judgment alone.")
        return

    record(session, "delegated_result", "potentia_response_obtained", potentia_formulation=potentia_response.potentia_formulation, rationale=potentia_response.rationale)
    print("\nPotentia's independent formulation: " + potentia_response.potentia_formulation)
    print("Potentia's rationale: " + potentia_response.rationale)