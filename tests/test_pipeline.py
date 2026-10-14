from types import SimpleNamespace

import clinical_pipeline
from session_record import start_session
from shared import (
    StructuredInput,
    SafetyScreening,
    SafetyScreeningResult,
    PotentiaResponse,
    MatchingOutcome,
    MatchingResult,
)


SAFE = SafetyScreening(result=SafetyScreeningResult.NONE)
URGENT = SafetyScreening(result=SafetyScreeningResult.URGENT_RETURN)
POTENTIA = PotentiaResponse(potentia_formulation="Vestibular migraine", rationale="Episodic vertigo with headache.")
MATCH = MatchingOutcome(result=MatchingResult.MATCH)
DIVERGENCE = MatchingOutcome(result=MatchingResult.DIVERGENCE)
ANALYSIS = SimpleNamespace(model_dump=lambda mode: {"decision_fork": "test"})


def run_case(monkeypatch, tmp_path, answers, safety=SAFE, potentia=POTENTIA, matching=DIVERGENCE, analysis=ANALYSIS):
    fake_results = {
        "run_safety_screening": safety,
        "get_potentia_response": potentia,
        "match_formulations": matching,
        "get_evidentiary_analysis": analysis,
    }
    monkeypatch.setattr(clinical_pipeline, "call_with_standby", lambda func, *args: fake_results[func.__name__])
    monkeypatch.setattr(clinical_pipeline, "render_analysis", lambda analysis: "ANALYSIS TEXT")

    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    session = start_session(tmp_path)
    case = StructuredInput(evidence_packet="Episodic vertigo.", potestas_formulation="Meniere disease")

    outcome = clinical_pipeline.run_pipeline(case, None, session)

    assert list(replies) == []
    return outcome, session


def event_names(session):
    return [event["event"] for event in session["events"]]


def rationale_stages(session):
    return [event["data"]["stage"] for event in session["events"] if event["event"] == "rationale_entered"]


def test_discrepancy_shows_potentia_before_analysis(monkeypatch, tmp_path, capsys):
    outcome, session = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "Keep my formulation."])
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == [
        "safety_screened",
        "evidence_presented",
        "formulation_confirmed",
        "potentia_response_obtained",
        "matching_classified",
        "rationale_entered",
        "matching_result_presented",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
        "report_obtained",
        "report_presented",
        "final_determination",
    ]
    assert rationale_stages(session) == ["pre_exposure"]
    assert "Potentia [Comparator]: divergence" in screen
    assert screen.index("Vestibular migraine") < screen.index("ANALYSIS TEXT")


def test_discrepancy_keeps_potentia_when_analysis_fails(monkeypatch, tmp_path, capsys):
    outcome, session = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "Keep my formulation."], analysis=None)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == [
        "safety_screened",
        "evidence_presented",
        "formulation_confirmed",
        "potentia_response_obtained",
        "matching_classified",
        "rationale_entered",
        "matching_result_presented",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
        "report_unavailable",
        "final_determination",
    ]
    assert "Potentia [Formulator], formulation: Vestibular migraine" in screen
    assert "Could not complete the comparative analysis." in screen


def test_convergence_full_path(monkeypatch, tmp_path, capsys):
    outcome, session = run_case(monkeypatch, tmp_path, ["y", "y", "My explanation.", "y", "Keep my formulation."], matching=MATCH)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == [
        "safety_screened",
        "evidence_presented",
        "formulation_confirmed",
        "potentia_response_obtained",
        "matching_classified",
        "matching_result_presented",
        "potentia_formulation_presented",
        "access_decided",
        "rationale_entered",
        "potentia_rationale_presented",
        "access_decided",
        "report_obtained",
        "report_presented",
        "final_determination",
    ]
    assert rationale_stages(session) == ["post_convergence_pre_rationale_exposure"]
    assert "Potentia [Comparator]: match" in screen


def test_suspended_discrepancy_without_explanation(monkeypatch, tmp_path):
    outcome, session = run_case(monkeypatch, tmp_path, ["y", "skip", "", "Keep my formulation."])

    assert outcome == "completed"
    assert event_names(session) == [
        "safety_screened",
        "evidence_presented",
        "formulation_confirmed",
        "potentia_response_obtained",
        "matching_classified",
        "prior_rationale_suspended",
        "matching_result_presented",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
        "access_decided",
        "final_determination",
    ]
    assert rationale_stages(session) == []