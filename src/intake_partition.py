import time
from google.genai import types
from shared import IntakePartition
from session_record import record


def run_intake(client, session):

    while True:
        raw_input_text = input("Enter the case (evidence and your formulation): ").strip()
        if raw_input_text:
            break
        print("Case text is required.")
    record(session, "human_input", "natural_text_entered", text=raw_input_text)

    config = types.GenerateContentConfig(
        system_instruction="You are a deterministic splitter of inputs that identifies and isolates, when present, subjective diagnostic inferences from case evidence and causal data (including inferences on causation). Clinical observations directly stated as facts (e.g. 'wounds consistent with X') are case evidence, not inference, even if they involve comparison to a known pattern. Only formulations attributable to the clinician performing the assessment count as potestas_formulation. Statements reporting a third party's belief or opinion (including the patient's own) belong to evidence_packet, as observed/reported data. Outputs in JSON",
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=IntakePartition,
    )

    print("\nPotentia [Intake Splitter] is separating the evidence from your formulation...")

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=raw_input_text,
                config=config,
            )
            partition = response.parsed

            if partition is None:
                raise ValueError("Intake returned no parsed partition.")

            record(session, "delegated_result", "intake_partitioned", evidence_packet=partition.evidence_packet, potestas_formulation=partition.potestas_formulation)
            return partition

        except Exception as e:
            print(f"Attempt {attempt+1}/3 failed: {e}")
            record(session, "runtime", "intake_attempt_failed", attempt=attempt + 1, error=str(e))
            time.sleep((attempt+1)*2)

    return None