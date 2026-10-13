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


SKIP_WORD = "skip"

EXPLANATION_POINTS = (
    "what evidence supports it, what would weaken or refute it, "
    "and what is still uncertain or missing."
)


def ask_grounds_or_suspend(branch):
    if branch == "convergence":
        withheld = "reasoning"
    else:
        withheld = "response"
    prompt = (
        f"\nExplain your formulation: {EXPLANATION_POINTS} "
        f"Needed before Potentia's {withheld} is shown. "
        f"Or type '{SKIP_WORD}' to see it now; your choice is recorded.\n> "
    )
    answer = ask_required(prompt)
    if answer.strip().lower() == SKIP_WORD:
        return None
    return answer


def show_matching(session, matching):
    print(f"\nPotentia [Comparator]: {matching.result.value.replace('_', ' ')}")
    record(session, "exposure", "matching_result_presented")


def show_formulation(session, potentia_response):
    print(f"\nPotentia [Formulator], formulation: {potentia_response.potentia_formulation}")
    record(session, "exposure", "potentia_formulation_presented")


def show_reasoning(session, potentia_response):
    print(f"\nPotentia [Formulator], reasoning: {potentia_response.rationale}")
    record(session, "exposure", "potentia_rationale_presented")


def run_comparative_analysis(session, case_input, potestas_response, potentia_response, client):
    evidentiary_analysis = call_with_standby(get_evidentiary_analysis, case_input.evidence_packet, potestas_response, potentia_response, client)

    if evidentiary_analysis is None:
        record(session, "runtime", "report_unavailable")
        print("\nCould not complete the comparative analysis.")
        return

    record(session, "delegated_result", "report_obtained", report=evidentiary_analysis.model_dump(mode="json"))
    print("\nPotentia [Analyst], comparative analysis:")
    print(render_analysis(evidentiary_analysis))
    record(session, "exposure", "report_presented")


def close_with_determination(session):
    final_determination = ask_required("\nYour final decision (keep, revise or defer your formulation): ")
    record(session, "human_input", "final_determination", text=final_determination)
    return "completed"


def run_suspended_access(session, case_input, potentia_response, matching, client, branch):
    record(session, "human_input", "prior_rationale_suspended", branch=branch)

    if branch != "convergence":
        if matching is not None:
            show_matching(session, matching)
        show_formulation(session, potentia_response)

    show_reasoning(session, potentia_response)

    post_rationale = input(
        f"\nExplain your formulation to get the comparative analysis: {EXPLANATION_POINTS} "
        "Your explanation will be recorded as written after Potentia's response. "
        "Press Enter to continue without the analysis.\n> "
    ).strip()
    record(session, "human_input", "access_decided", access="comparative_analysis", granted=bool(post_rationale))

    if not post_rationale:
        return close_with_determination(session)

    potestas_response = PotestasResponse(
        potestas_formulation=case_input.potestas_formulation,
        rationale=post_rationale,
        rationale_stage=RationaleStage.POST_POTENTIA_RATIONALE_EXPOSURE,
    )
    record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=post_rationale)

    run_comparative_analysis(session, case_input, potestas_response, potentia_response, client)
    return close_with_determination(session)


def run_pipeline(case_input, client, session):
    if not case_input.evidence_packet:
        print("Evidence is required. Session closed.")
        return "cancelled"

    screening = call_with_standby(run_safety_screening, case_input.evidence_packet, client)

    if screening is None:
        record(session, "runtime", "safety_unavailable")
        print("Safety check unavailable. Continue with your own clinical judgment.")
        return "failed"

    record(session, "delegated_result", "safety_screened", result=screening.result.value)

    if screening.result == SafetyScreeningResult.URGENT_RETURN:
        print("\nURGENCY FLAGGED. The second-opinion steps stop here. You decide how to proceed.")
        record(session, "exposure", "urgency_flag_presented")

        override = input("\nSee Potentia's response now (Break-Glass)? (y/n): ")
        invoked = override.strip().lower() in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "break_glass_decided", answer=override.strip(), invoked=invoked)

        if invoked:
            potentia_response = call_with_standby(get_potentia_response, case_input.evidence_packet, client)

            if potentia_response is None:
                record(session, "runtime", "potentia_response_unavailable")
                print("Potentia is unavailable. Continue with your own clinical judgment.")
            else:
                record(session, "delegated_result", "potentia_response_obtained", potentia_formulation=potentia_response.potentia_formulation, rationale=potentia_response.rationale)
                show_formulation(session, potentia_response)
                show_reasoning(session, potentia_response)

        return "safety_return"

    if not case_input.potestas_formulation:
        print("A second opinion needs your own formulation. Session closed.")
        return "cancelled"

    print(f"\nEvidence: {case_input.evidence_packet}")
    record(session, "exposure", "evidence_presented")

    confirmation = ask_confirmation(case_input.potestas_formulation)

    if confirmation.strip().lower() not in AFFIRMATIVE_RESPONSES:
        record(session, "human_input", "formulation_rejected", answer=confirmation.strip())
        print("Formulation not confirmed. Start a new session to revise it.")
        return "cancelled"

    record(session, "human_input", "formulation_confirmed", formulation=case_input.potestas_formulation)

    potentia_response = call_with_standby(get_potentia_response, case_input.evidence_packet, client)

    if potentia_response is None:
        record(session, "runtime", "potentia_response_unavailable")
        print("Potentia is unavailable. Try again later.")
        return "failed"

    record(session, "delegated_result", "potentia_response_obtained", potentia_formulation=potentia_response.potentia_formulation, rationale=potentia_response.rationale)

    matching = call_with_standby(match_formulations, case_input.potestas_formulation, potentia_response.potentia_formulation, client)

    if matching is None:
        record(session, "runtime", "matching_unavailable")
        print("\nCould not compare the two formulations. Potentia's response is still available.")

        access_response = input(
            "\nSee Potentia's response and the comparative analysis? "
            "You will be asked to explain your formulation first. (y/n): "
        ).strip().lower()
        granted = access_response in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "access_decided", access="response_and_analysis", answer=access_response, granted=granted)

        if not granted:
            return close_with_determination(session)

        potestas_rationale = ask_grounds_or_suspend("matching_unavailable")
        if potestas_rationale is None:
            return run_suspended_access(session, case_input, potentia_response, matching, client, "matching_unavailable")

        potestas_response = PotestasResponse(
            potestas_formulation=case_input.potestas_formulation,
            rationale=potestas_rationale,
            rationale_stage=RationaleStage.PRE_EXPOSURE,
        )
        record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=potestas_rationale)

        show_formulation(session, potentia_response)
        show_reasoning(session, potentia_response)
        run_comparative_analysis(session, case_input, potestas_response, potentia_response, client)
        return close_with_determination(session)

    record(session, "delegated_result", "matching_classified", result=matching.result.value)

    if matching.result == MatchingResult.MATCH:
        show_matching(session, matching)
        show_formulation(session, potentia_response)

        go_deeper = input(
            "\nSee Potentia's full reasoning? "
            "You will be asked to explain your formulation first. (y/n): "
        ).strip().lower()
        reasoning_granted = go_deeper in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "access_decided", access="full_reasoning", answer=go_deeper, granted=reasoning_granted)

        if not reasoning_granted:
            return close_with_determination(session)

        post_convergence_rationale = ask_grounds_or_suspend("convergence")
        if post_convergence_rationale is None:
            return run_suspended_access(session, case_input, potentia_response, matching, client, "convergence")

        potestas_response = PotestasResponse(
            potestas_formulation=case_input.potestas_formulation,
            rationale=post_convergence_rationale,
            rationale_stage=RationaleStage.POST_CONVERGENCE_PRE_RATIONALE_EXPOSURE,
        )
        record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=post_convergence_rationale)

        show_reasoning(session, potentia_response)

        access_report = input("\nSee the comparative analysis? (y/n): ").strip().lower()
        report_granted = access_report in AFFIRMATIVE_RESPONSES
        record(session, "human_input", "access_decided", access="comparative_analysis", answer=access_report, granted=report_granted)

        if not report_granted:
            return close_with_determination(session)

        run_comparative_analysis(session, case_input, potestas_response, potentia_response, client)
        return close_with_determination(session)

    potestas_rationale = ask_grounds_or_suspend("discrepancy")
    if potestas_rationale is None:
        return run_suspended_access(session, case_input, potentia_response, matching, client, "discrepancy")

    potestas_response = PotestasResponse(
        potestas_formulation=case_input.potestas_formulation,
        rationale=potestas_rationale,
        rationale_stage=RationaleStage.PRE_EXPOSURE,
    )
    record(session, "human_input", "rationale_entered", stage=potestas_response.rationale_stage.value, text=potestas_rationale)

    show_matching(session, matching)
    show_formulation(session, potentia_response)
    show_reasoning(session, potentia_response)
    run_comparative_analysis(session, case_input, potestas_response, potentia_response, client)
    return close_with_determination(session)
