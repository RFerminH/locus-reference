import time
from google.genai import types
from shared import SafetyScreening, SafetyScreeningResult


def run_safety_screening(evidence_packet, client):
    screening_config = types.GenerateContentConfig(
        system_instruction=(
            "You are a narrowly scoped clinical safety screener. "
            "Your sole task is to determine whether the supplied case evidence activates "
            "the reserved urgent-return condition: a time-critical situation in which completing "
            "the ordinary Pairing Hold and second-opinion sequence before returning control "
            "to the clinician could introduce a clinically material delay. "
            "Use clinical inference only as far as needed to decide whether that condition is "
            "activated, and return only the classification. "
            "Return urgent_return only when the supplied evidence itself supports immediate return "
            "to the clinician before the ordinary second-opinion flow continues. "
            "Otherwise return none."
        ),
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=SafetyScreening,
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=evidence_packet,
                config=screening_config,
            )
            return response.parsed
        except Exception as e:
            print(f"Attempt to connect {attempt+1}/3 failed: '{e}'")
            time.sleep((attempt+1)*2)

    return None