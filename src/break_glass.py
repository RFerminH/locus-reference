from evidentiary_return import get_potentia_response 

def run_break_glass(client):
    print("Break-Glass invoked. Ordinary Pairing Hold sequence bypassed by explicit Potestas decision.")

    raw_evidence=input("Enter case evidence: ").strip()
    if not raw_evidence:
        print("No evidence supplied. Nothing to evaluate.")
        return
    
    potentia_response= get_potentia_response(raw_evidence,client)
    if potentia_response is None:
        print("Unable to obtain Potentia's independent clinical support. Proceed with clinical judgment alone.")

    else:
        print(potentia_response)
