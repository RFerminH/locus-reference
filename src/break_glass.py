from evidentiary_return import get_potentia_response
from session_record import record


def run_break_glass(client, session):
    print("Break-Glass on. Potentia's response will be shown directly.")
    record(session, "human_input", "break_glass_invoked", route="direct")

    raw_evidence = input("Enter the evidence: ").strip()
    if not raw_evidence:
        print("No evidence entered. Session closed.")
        record(session,"runtime", "break_glass_closed", reason="no_evidence")
        return "cancelled"
    record(session, "human_input", "evidence_entered", text=raw_evidence)

    print("\nPotentia [Formulator] is proposing its own formulation from the evidence...")


    potentia_response = get_potentia_response(raw_evidence, client)

    if potentia_response is None:
        record(session, "runtime", "potentia_response_unavailable")
        print("Potentia is unavailable. Continue with your own clinical judgment.")
        return "failed"

    record(session, "delegated_result", "potentia_response_obtained", potentia_formulation=potentia_response.potentia_formulation, rationale=potentia_response.rationale)
    print("\nPotentia [Formulator], formulation: " + potentia_response.potentia_formulation)
    record(session, "exposure", "potentia_formulation_presented")
    print("\nPotentia [Formulator], reasoning: " + potentia_response.rationale)
    record(session, "exposure", "potentia_rationale_presented")
    return "break_glass_return"