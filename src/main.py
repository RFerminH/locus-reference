import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

client=genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class IntakePartition(BaseModel):
    evidence_packet:str=Field(description="Objective, observable data only (symptoms, timeline, measurable facts). No interpretation or diagnosis.")
    initial_formulation:str=Field(description="Subjective inference, suspicion, or diagnostic reasoning present in the input. Empty string if none is present")
    
config=types.GenerateContentConfig(
    system_instruction="You are a deterministic intake classifier for a clinical context. Separate the input into two categories: objective, observable data (symptoms, timeline, measurable facts) versus subjective inference or diagnostic reasoning (suspicions, interpretations, conclusions). Do not add information that was not present in the input. Output must be valid JSON matching the given schema.",
    response_mime_type="application/json",
    response_schema=IntakePartition,
    temperature=0.2,
    )


for intent in range(3):

    try:
        response=client.models.generate_content(
            model="gemini-3.6-flash",
            contents="Female, 45, two days of worsening right-sided abdominal pain, low-grade fever, nausea. No prior surgical history. Presentation consistent with acute appendicitis, though ovarian pathology has not been ruled out.",
            config=config,
            )

        result=response.parsed
        print(result)

        if result.initial_formulation:
            print("Potestas formulation found. Elaborating pairing Potentia formulation...")

        else:
            print("Human cognitive elaboration not found. Awaiting Potestas formulation.")

        break

    except Exception as e:
        print(f"Attempt({intent+1}) failed {e}")
        time.sleep((intent+1)*2)