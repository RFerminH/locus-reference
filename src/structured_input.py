from shared import StructuredInput


def run_structured(client=None):
    while True:
        data = input("Enter evidentiary data: ").strip()
        if data:
            break
        print("Evidentiary data required to proceed.")

    while True:
        inferences = input("Enter potestas (your) formulation: ").strip()
        if inferences:
            break
        print("Potestas formulation required to proceed.")

    return StructuredInput(evidence_packet=data, potestas_formulation=inferences)


if __name__ == "__main__":
    print(run_structured())