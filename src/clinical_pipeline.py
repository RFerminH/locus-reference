from shared import (
    AFFIRMATIVE_RESPONSES,
    ask_confirmation,
    ask_required,
    SafetyScreeningResult,
    MatchingResult,
    PotestasResponse,
    RationaleStage,
    call_with_standby,
)
from session_record import record
from safety_potentia import run_safety_screening
from evidentiary_return import get_potentia_response, match_formulations
from evidentiary_potentia import get_evidentiary_analysis
from analysis_display import render_analysis


def run_pipeline(case_input, client, session):
    if not case_input.evidence_packet:
        print("Case evidence required.")
        return None
    

    screening = call_with_standby(run_safety_screening, case_input.evidence_packet, client)

    if screening is None:
        record(session, "runtime", "safety_unavailable")
        print("Safety screening unavailable. Control returns to the clinician.")
        return None
    
    record(session, "delegated_result", "safety_screened", result=screening.result.value)


    if screening.result == SafetyScreeningResult.URGENT_RETURN:
        print("URGENCY FLAGGED. Reserved Safety Return: the time-critical return condition has been activated.\nThe second-opinion flow is suspended and control returns to Potestas.")
        record(session, "exposure", "urgency_flag_presented")

        override = input("\n\nBreak-Glass (bypasses Pairing Hold, exposes Potentia's reading)? (y/n): ")
        invoked = override.strip().lower() in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "break_glass_decided", answer=override.strip(), invoked=invoked)

        if invoked:
            potentia_response = call_with_standby(get_potentia_response, case_input.evidence_packet, client)

            if potentia_response is None:
                record(session, "runtime", "potentia_response_unavailable")
                print("Unable to obtain Potentia's independent clinical support. Proceed with clinical judgment alone.")

            else:
                record(session, "delegated_result", "potentia_response_obtained", potentia_formulation=potentia_response.potentia_formulation, rationale=potentia_response.rationale)
                print(f"\nPotentia's independent formulation: {potentia_response.potentia_formulation}")
                record(session, "exposure", "potentia_formulation_presented")
                print(f"\nPotentia's rationale: {potentia_response.rationale}")
                record(session, "exposure", "potentia_rationale_presented")

        return None

    if not case_input.potestas_formulation:
        print("A second opinion requires your own diagnostic formulation.")
        return None

    print(f"Evidence as partitioned: {case_input.evidence_packet}")
    record(session, "exposure", "evidence_presented")
    
    confirmation = ask_confirmation(case_input.potestas_formulation)

    if confirmation.strip().lower() not in AFFIRMATIVE_RESPONSES:
        record(session, "human_input", "formulation_rejected", answer=confirmation.strip())
        print("Revise or rewrite your formulation.")
        return None
    
    record(session, "human_input", "formulation_confirmed", formulation=case_input.potestas_formulation)

    potentia_response = call_with_standby(get_potentia_response, case_input.evidence_packet, client)

    if potentia_response is None:
        record(session, "runtime", "potentia_response_unavailable")
        print("Unable to obtain Potentia's independent clinical support. Try again later.")
        return None

    record(session, "delegated_result", "potentia_response_obtained", potentia_formulation=potentia_response.potentia_formulation, rationale=potentia_response.rationale)

    matching = call_with_standby(match_formulations, case_input.potestas_formulation, potentia_response.potentia_formulation, client)

    if matching is None:
        record(session, "runtime", "matching_unavailable")
        print(
            "Unable to classify the relationship between the formulations. "
            "Potentia's independent response remains available."
        )

        access_response = input(
            "\n\nAccess Potentia's independent response and request a direct comparative evidentiary analysis? "
            "You will be asked to state your own grounds before Potentia's response is shown. (y/n): ").strip().lower()
        
        granted = access_response in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "access_decided", access="response_and_analysis", answer=access_response, granted=granted)

        if not granted:
            final_determination = ask_required("Retain, revise, or defer your formulation: ")
            return final_determination

        potestas_rationale = ask_required("Before viewing Potentia's formulation or reasoning, state what evidence supports your formulation, what would weaken or refute it, and what remains uncertain or missing: ")
        
        potestas_response = PotestasResponse(
            potestas_formulation=case_input.potestas_formulation,
            rationale=potestas_rationale,
            rationale_stage=RationaleStage.PRE_EXPOSURE,
        )
        record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=potestas_rationale)

        evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

        print(f"\nPotentia's independent formulation: {potentia_response.potentia_formulation}")
        record(session, "exposure", "potentia_formulation_presented")
        print(f"Potentia's rationale: {potentia_response.rationale}")
        record(session, "exposure", "potentia_rationale_presented")


        if evidentiary_analysis is not None:
            print("\nDirect comparative evidentiary analysis:")
            print(render_analysis(evidentiary_analysis))

        else:
            print(
                "\nUnable to complete the direct comparative evidentiary "
                "analysis. The two original responses remain available."
            )

        final_determination = ask_required("\nFinal determination by Potestas: ")
        return final_determination
    record(session, "delegated_result", "matching_classified", result=matching.result.value)
    
    if matching.result == MatchingResult.MATCH:
        print(f"\nMatching result: {matching.result.value}")
        record(session, "exposure", "matching_result_presented")
        print(f"Potentia's independent formulation: {potentia_response.potentia_formulation}")
        record(session, "exposure", "potentia_formulation_presented")

        go_deeper = input("\n\nAccess Potentia's full reasoning? You will be asked to state your own grounds first, before Potentia's reasoning is shown. (y/n): ").strip().lower()
        reasoning_granted = go_deeper in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "access_decided", access="full_reasoning", answer=go_deeper, granted=reasoning_granted)

        if not reasoning_granted:
            final_determination = ask_required("Retain, revise, or defer your formulation: ")
            return final_determination

        post_convergence_rationale = ask_required(
                "State what evidence supports your formulation, "
                "what would weaken or refute it, "
                "and what remains uncertain or missing: "
            )
        potestas_response = PotestasResponse(
            potestas_formulation=case_input.potestas_formulation,
            rationale=post_convergence_rationale,
            rationale_stage=RationaleStage.POST_CONVERGENCE_PRE_RATIONALE_EXPOSURE,
        )

        record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=post_convergence_rationale)

        print(f"\nPotentia's rationale: {potentia_response.rationale}")
        record(session, "exposure", "potentia_rationale_presented")

        access_report = input("\n\nAccess the full comparative evidentiary analysis? (y/n): ").strip().lower()
        report_granted = access_report in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "access_decided", access="comparative_analysis", answer=access_report, granted=report_granted)

        if not report_granted:
            final_determination = ask_required("Retain, revise, or defer your formulation after reviewing Potentia's reasoning: ")
            return final_determination

        evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

        if evidentiary_analysis is None:
            print(
                "Unable to complete the comparative evidentiary analysis. "
                "The formulations and rationales remain available. "
                "Control returns to Potestas."
            )
            final_determination = ask_required(
                    "Retain, revise, or defer your formulation based on the "
                    "information currently available: "
                )
            return final_determination

        print("\nComparative evidentiary analysis:")
        print(render_analysis(evidentiary_analysis))
    

        final_determination = ask_required("\n\nFinal determination by Potestas: ")
        return final_determination

    potestas_rationale = ask_required(
            "Before viewing Potentia's formulation or reasoning, state what evidence "
            "supports your formulation, what would weaken or refute it, and what "
            "remains uncertain or missing: "
        )

    potestas_response = PotestasResponse(
        potestas_formulation=case_input.potestas_formulation,
        rationale=potestas_rationale,
        rationale_stage=RationaleStage.PRE_EXPOSURE,
    )

    record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=potestas_rationale)

    evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

    if evidentiary_analysis is None:
        print(
            "Unable to complete the comparative evidentiary analysis. "
            "The independent formulation and matching result remain available."
        )
        print(f"\nMatching result: {matching.result.value}")
        record(session, "exposure", "matching_result_presented")

        print(f"Potentia's independent formulation: {potentia_response.potentia_formulation}")
        record(session, "exposure", "potentia_formulation_presented")

        print(f"Potentia's rationale: {potentia_response.rationale}")
        record(session, "exposure", "potentia_rationale_presented")

        final_determination = ask_required(
                "\n\nRetain, revise, or defer your formulation based on the "
                "information currently available: "
            )
        return final_determination

    print(f"\nMatching result: {matching.result.value}")
    record(session, "exposure", "matching_result_presented")

    print(f"Potentia's independent formulation: {potentia_response.potentia_formulation}")
    record(session, "exposure", "potentia_formulation_presented")

    print(f"Potentia's rationale: {potentia_response.rationale}")
    record(session, "exposure", "potentia_rationale_presented")
    
    print("\nComparative evidentiary analysis:")
    print(render_analysis(evidentiary_analysis))

    final_determination = ask_required("\nFinal determination by Potestas: ")
    return final_determination