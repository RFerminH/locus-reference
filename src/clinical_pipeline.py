from shared import (
    AFFIRMATIVE_RESPONSES,
    ask_confirmation,
    SafetyScreeningResult,
    MatchingResult,
    PotestasResponse,
    RationaleStage,
    call_with_standby,
)
from safety_potentia import run_safety_screening
from evidentiary_return import get_potentia_response, match_formulations
from evidentiary_potentia import get_evidentiary_analysis
from analysis_display import render_analysis


def run_pipeline(case_input, client):
    if not case_input.evidence_packet:
        print("Case evidence required.")
        return None

    screening = call_with_standby(run_safety_screening, case_input.evidence_packet, client)

    if screening is None:
        print("Safety screening unavailable. Control returns to the clinician.")
        return None

    if screening.result == SafetyScreeningResult.URGENT_RETURN:
        print("URGENCY FLAGGED. Reserved Safety Return: the time-critical return condition has been activated.\nThe second-opinion flow is suspended and control returns to Potestas.")

        override = input("\n\nBreak-Glass (bypasses Pairing Hold, exposes Potentia's reading)? (y/n): ")
        if override.strip().lower() in AFFIRMATIVE_RESPONSES:
            potentia_response = call_with_standby(get_potentia_response, case_input.evidence_packet, client)

            if potentia_response is None:
                print("Unable to obtain Potentia's independent clinical support. Proceed with clinical judgment alone.")
            else:
                print(potentia_response)
        return None

    if not case_input.potestas_formulation:
        print("A second opinion requires your own diagnostic formulation.")
        return None

    print(f"Evidence as partitioned: {case_input.evidence_packet}")

    confirmation = ask_confirmation(case_input.potestas_formulation)

    if confirmation.strip().lower() not in AFFIRMATIVE_RESPONSES:
        print("Revise or rewrite your formulation.")
        return None

    potentia_response = call_with_standby(get_potentia_response, case_input.evidence_packet, client)

    if potentia_response is None:
        print("Unable to obtain Potentia's independent clinical support. Try again later.")
        return None

    matching = call_with_standby(match_formulations, case_input.potestas_formulation, potentia_response.potentia_formulation, client)

    if matching is None:
        print(
            "Unable to classify the relationship between the formulations. "
            "Potentia's independent response remains available."
        )

        access_response = input(
            "\n\nAccess Potentia's independent response and request a direct comparative evidentiary analysis? "
            "You will be asked to state your own grounds before Potentia's response is shown. (y/n): ").strip().lower()

        if access_response not in AFFIRMATIVE_RESPONSES:
            final_determination = ""
            while not final_determination:
                final_determination = input("Retain, revise, or defer your formulation: ").strip()
            return final_determination

        potestas_rationale = ""
        while not potestas_rationale:
            potestas_rationale = input("Before viewing Potentia's formulation or reasoning, state what evidence supports your formulation, what would weaken or refute it, and what remains uncertain or missing: ").strip()

        potestas_response = PotestasResponse(
            potestas_formulation=case_input.potestas_formulation,
            rationale=potestas_rationale,
            rationale_stage=RationaleStage.PRE_EXPOSURE,
        )

        evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

        print(f"\nPotentia's independent formulation: {potentia_response.potentia_formulation}")
        print(f"Potentia's rationale: {potentia_response.rationale}")

        if evidentiary_analysis is not None:
            print("\nDirect comparative evidentiary analysis:")
            print(render_analysis(evidentiary_analysis))
        else:
            print(
                "\nUnable to complete the direct comparative evidentiary "
                "analysis. The two original responses remain available."
            )

        final_determination = ""
        while not final_determination:
            final_determination = input("\nFinal determination by Potestas: ").strip()
        return final_determination

    if matching.result == MatchingResult.MATCH:
        print("\nFormulations converge.")
        print(f"Potentia's independent formulation: {potentia_response.potentia_formulation}")

        go_deeper = input("\n\nAccess Potentia's full reasoning? You will be asked to state your own grounds first, before Potentia's reasoning is shown. (y/n): ").strip().lower()

        if go_deeper not in AFFIRMATIVE_RESPONSES:
            final_determination = ""
            while not final_determination:
                final_determination = input("Retain, revise, or defer your formulation: ").strip()
            return final_determination

        post_convergence_rationale = ""
        while not post_convergence_rationale:
            post_convergence_rationale = input(
                "State what evidence supports your formulation, what would weaken or refute it, and what remains uncertain or missing: "
            ).strip()

        potestas_response = PotestasResponse(
            potestas_formulation=case_input.potestas_formulation,
            rationale=post_convergence_rationale,
            rationale_stage=RationaleStage.POST_CONVERGENCE_PRE_RATIONALE_EXPOSURE,
        )

        print(f"\nPotentia's rationale: {potentia_response.rationale}")

        access_report = input("\n\nAccess the full comparative evidentiary analysis? (y/n): ").strip().lower()

        if access_report not in AFFIRMATIVE_RESPONSES:
            final_determination = ""
            while not final_determination:
                final_determination = input("Retain, revise, or defer your formulation after reviewing Potentia's reasoning: ").strip()
            return final_determination

        evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

        if evidentiary_analysis is None:
            print(
                "Unable to complete the comparative evidentiary analysis. "
                "The formulations and rationales remain available. "
                "Control returns to Potestas."
            )
            final_determination = ""
            while not final_determination:
                final_determination = input(
                    "Retain, revise, or defer your formulation based on the "
                    "information currently available: "
                ).strip()
            return final_determination

        print("\nComparative evidentiary analysis:")
        print(render_analysis(evidentiary_analysis))
        print(evidentiary_analysis.unsupported_or_overextended_claims)

        final_determination = ""
        while not final_determination:
            final_determination = input("\n\nFinal determination by Potestas: ").strip()
        return final_determination

    potestas_rationale = ""
    while not potestas_rationale:
        potestas_rationale = input(
            "Before viewing Potentia's formulation or reasoning, state what evidence "
            "supports your formulation, what would weaken or refute it, and what "
            "remains uncertain or missing: "
        ).strip()

    potestas_response = PotestasResponse(
        potestas_formulation=case_input.potestas_formulation,
        rationale=potestas_rationale,
        rationale_stage=RationaleStage.PRE_EXPOSURE,
    )

    evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

    if evidentiary_analysis is None:
        print(
            "Unable to complete the comparative evidentiary analysis. "
            "The independent formulation and matching result remain available."
        )
        print(f"\nMatching result: {matching.result.value}")
        print(f"Potentia's independent formulation: {potentia_response.potentia_formulation}")
        print(f"Potentia's rationale: {potentia_response.rationale}")

        final_determination = ""
        while not final_determination:
            final_determination = input(
                "\n\nRetain, revise, or defer your formulation based on the "
                "information currently available: "
            ).strip()
        return final_determination

    print(f"\nMatching result: {matching.result.value}")
    print(f"Potentia's independent formulation: {potentia_response.potentia_formulation}")
    print(f"Potentia's rationale: {potentia_response.rationale}")

    print("\nComparative evidentiary analysis:")
    print(render_analysis(evidentiary_analysis))
    print(evidentiary_analysis.unsupported_or_overextended_claims)

    final_determination = ""
    while not final_determination:
        final_determination = input("\nFinal determination by Potestas: ").strip()
    return final_determination