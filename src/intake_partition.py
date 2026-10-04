import time
from google.genai import types
from shared import IntakePartition



def run_intake(client):

    while True:
        raw_input_text=input("Enter the clinical input composed by evidentiary data and formulation: ").strip()
        if raw_input_text:
            break
        print("Clinical input required to proceed.")

    config = types.GenerateContentConfig(
        system_instruction="You are a deterministic splitter of inputs that identifies and isolates, when present, subjective diagnostic inferences from case evidence and causal data (including inferences on causation). Clinical observations directly stated as facts (e.g. 'wounds consistent with X') are case evidence, not inference, even if they involve comparison to a known pattern. Only formulations attributable to the clinician performing the assessment count as potestas_formulation. Statements reporting a third party's belief or opinion (including the patient's own) belong to evidence_packet, as observed/reported data. Outputs in JSON",
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=IntakePartition,
    )
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=raw_input_text,
                config=config,
            )

            return response.parsed

        except Exception as e:
            print(f"Attempt {attempt+1}/3 failed: {e}")
            time.sleep((attempt+1)*2)

    return None
        
        
