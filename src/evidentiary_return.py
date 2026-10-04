import time
from google.genai import types
from shared import PotentiaResponse, MatchingOutcome

def get_potentia_response(evidence_packet, client):
    potentia_config = types.GenerateContentConfig(
        system_instruction=(
            "You are a clinical analyst. Based solely on the evidence provided, produce an independent diagnostic formulation, "
            "with supporting reasoning. Evidence may include directly observed "
            "findings, reported symptoms, behavioral observations, or patterns described over time — "
            "treat all evidence types as legitimate grounds for a formulation, evaluated on their own terms. "
            "Clearly distinguish supplied evidence from inferences drawn from it. "
            "Do not introduce clinical findings that were not present in the evidence."
        ),
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=PotentiaResponse,
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=evidence_packet,
                config=potentia_config,
            )
            return response.parsed
        
        except Exception as e:
            print(f"Attempt {attempt+1}/3 failed: {e}")
            time.sleep((attempt+1)*2)

    return None



def match_formulations(formulation_a, formulation_b, client):
    match_config=types.GenerateContentConfig(
        system_instruction=(            
                "You are a diagnostic matching classifier. "
                "Compare Formulation A and Formulation B exclusively at the level of diagnostic conclusion. "
                "Do not assess which formulation is more accurate, better supported, safer, more urgent, "
                "or more clinically appropriate. Do not use treatment, management, severity, prognosis, "
                "urgency, or other downstream implications as matching criteria. "

                "Return MATCH when both formulations express the same diagnostic conclusion, "
                "allowing for different terminology or non-material wording. "

                "Return PARTIAL_MATCH only when multiple explicit diagnostic candidates are present "
                "and the candidate sets share at least one equivalent diagnosis without being equivalent overall. "

                "Do not return PARTIAL_MATCH merely because one formulation is broader, narrower, more specific, "
                "or belongs to the same diagnostic class, mechanism, or etiology as the other. "
                "In such cases, return DIVERGENCE unless the same diagnostic conclusion is explicitly shared. "

                "Return DIVERGENCE when the formulations do not express an equivalent diagnostic conclusion. "

                "Examples: "
                "'viral infection' vs 'rabies' -> DIVERGENCE. "
                "['rabies', 'viral encephalitis'] vs ['rabies', 'tetanus'] -> PARTIAL_MATCH. "

                "Do not infer diagnoses that are not explicitly present in either formulation. "
                "Classify only the diagnostic relationship between the two formulations."
        ),

        temperature=0.2,
        response_mime_type="application/json",
        response_schema=MatchingOutcome,
    )

    for attempt in range(3):
        try:                 
            response=client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"Formulation A: {formulation_a}\nFormulation B: {formulation_b}",
                config=match_config,
            )

            return response.parsed

        except Exception as e:
            print(f"Attempt {attempt+1}/3 to connect failed: {e}")
            time.sleep((attempt+1)*2)

    return None