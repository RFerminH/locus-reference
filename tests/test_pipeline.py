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
POTENTIA = PotentiaResponse(
    potentia_formulation="Vestibular migraine",
    rationale="Episodic vertigo with headache.",
    differential=["Benign paroxysmal positional vertigo"],
)
MATCH = MatchingOutcome(result=MatchingResult.MATCH)
DIVERGENCE = MatchingOutcome(result=MatchingResult.DIVERGENCE)
ANALYSIS = SimpleNamespace(model_dump=lambda mode: {"decision_fork": "test"})

BEFORE_ACCESS = [
    "safety_screened",
    "evidence_presented",
    "formulation_confirmed",
    "potentia_response_obtained",
]
COMPONENTS_BEFORE_ACCESS = ["run_safety_screening", "get_potentia_response", "match_formulations"]


def run_case(
        monkeypatch, 
        tmp_path, 
        answers, 
        safety=SAFE, 
        potentia=POTENTIA, 
        matching=DIVERGENCE, 
        analysis=ANALYSIS
    ):
    
    fake_results = {
        "run_safety_screening": safety,
        "get_potentia_response": potentia,
        "match_formulations": matching,
        "get_evidentiary_analysis": analysis,
    }
    calls = []

    def fake_call(func, *args):
        calls.append(func.__name__)
        return fake_results[func.__name__]

    monkeypatch.setattr(clinical_pipeline, "call_with_standby", fake_call)
    monkeypatch.setattr(clinical_pipeline, "render_analysis", lambda analysis: "ANALYSIS TEXT")

    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    session = start_session(tmp_path)

    case = StructuredInput(
        evidence_packet="Episodic vertigo.", 
        potestas_formulation="Meniere disease"
    )

    outcome = clinical_pipeline.run_pipeline(case, None, session)

    assert list(replies) == []
    return outcome, session, calls


def event_names(session):
    return [event["event"] for event in session["events"]]


def rationale_stages(session):
    return [event["data"]["stage"] for event in session["events"] if event["event"] == "rationale_entered"]


# Discrepancy: explain / skip / decline


def test_discrepancy_explain(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "Keep my formulation."])
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
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
    assert calls == COMPONENTS_BEFORE_ACCESS + ["get_evidentiary_analysis"]
    assert "Potentia [Comparator]: divergence" in screen
    assert screen.index("Vestibular migraine") < screen.index("ANALYSIS TEXT")


def test_discrepancy_explain_analysis_fails(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "Keep my formulation."], analysis=None)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
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


def test_discrepancy_skip(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "skip", "Keep my formulation."])
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "prior_rationale_suspended",
        "matching_result_presented",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
        "final_determination",
    ]
    assert rationale_stages(session) == []
    assert calls == COMPONENTS_BEFORE_ACCESS
    assert "Potentia [Formulator], reasoning" in screen
    assert "Potentia [Formulator], differential: Benign paroxysmal positional vertigo" in screen
    assert [event["data"] for event in session["events"] if event["event"] == "potentia_rationale_presented"] == [{"differential_presented": True}]    


def test_discrepancy_decline_with_no(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "no", "Keep my formulation."])
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "access_decided",
        "final_determination",
    ]
    assert calls == COMPONENTS_BEFORE_ACCESS
    assert "Potentia [" not in screen


def test_discrepancy_decline_with_enter(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "", "Keep my formulation."])
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "access_decided",
        "final_determination",
    ]
    assert calls == COMPONENTS_BEFORE_ACCESS
    assert "Potentia [" not in screen


# Convergence: explain / skip / decline


def test_convergence_explain(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "y", "Keep my formulation."], matching=MATCH)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "matching_result_presented",
        "potentia_formulation_presented",
        "rationale_entered",
        "potentia_rationale_presented",
        "access_decided",
        "report_obtained",
        "report_presented",
        "final_determination",
    ]
    assert rationale_stages(session) == ["post_convergence_pre_rationale_exposure"]
    assert calls == COMPONENTS_BEFORE_ACCESS + ["get_evidentiary_analysis"]
    assert "Potentia [Comparator]: match" in screen


def test_convergence_explain_report_declined(monkeypatch, tmp_path):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "n", "Keep my formulation."], matching=MATCH)

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "matching_result_presented",
        "potentia_formulation_presented",
        "rationale_entered",
        "potentia_rationale_presented",
        "access_decided",
        "final_determination",
    ]
    assert calls == COMPONENTS_BEFORE_ACCESS


def test_convergence_skip(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "skip", "Keep my formulation."], matching=MATCH)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "matching_result_presented",
        "potentia_formulation_presented",
        "prior_rationale_suspended",
        "potentia_rationale_presented",
        "final_determination",
    ]
    assert rationale_stages(session) == []
    assert calls == COMPONENTS_BEFORE_ACCESS
    assert "Potentia [Formulator], reasoning" in screen


def test_convergence_decline(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "", "Keep my formulation."], matching=MATCH)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_classified",
        "matching_result_presented",
        "potentia_formulation_presented",
        "access_decided",
        "final_determination",
    ]
    assert calls == COMPONENTS_BEFORE_ACCESS
    assert "Potentia [Formulator], formulation" in screen
    assert "Potentia [Formulator], reasoning" not in screen
    assert "differential" not in screen


# Comparator unavailable: explain / skip / decline


def test_matching_unavailable_explain(monkeypatch, tmp_path):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "My explanation.", "Keep my formulation."], matching=None)

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_unavailable",
        "rationale_entered",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
        "report_obtained",
        "report_presented",
        "final_determination",
    ]
    assert rationale_stages(session) == ["pre_exposure"]
    assert calls == COMPONENTS_BEFORE_ACCESS + ["get_evidentiary_analysis"]


def test_matching_unavailable_skip(monkeypatch, tmp_path):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "skip", "Keep my formulation."], matching=None)

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_unavailable",
        "prior_rationale_suspended",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
        "final_determination",
    ]
    assert calls == COMPONENTS_BEFORE_ACCESS


def test_matching_unavailable_decline(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y", "no", "Keep my formulation."], matching=None)
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert event_names(session) == BEFORE_ACCESS + [
        "matching_unavailable",
        "access_decided",
        "final_determination",
    ]
    assert calls == COMPONENTS_BEFORE_ACCESS
    assert "Potentia [Formulator]" not in screen

    

# Urgency, rejection and unavailable components


def test_urgency_break_glass(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y"], safety=URGENT)
    screen = capsys.readouterr().out

    assert outcome == "safety_return"
    assert event_names(session) == [
        "safety_screened",
        "urgency_flag_presented",
        "break_glass_decided",
        "potentia_response_obtained",
        "potentia_formulation_presented",
        "potentia_rationale_presented",
    ]
    assert calls == ["run_safety_screening", "get_potentia_response"]
    assert "URGENCY FLAGGED" in screen
    assert "Potentia [Formulator], formulation: Vestibular migraine" in screen


def test_urgency_no_break_glass(monkeypatch, tmp_path, capsys):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["n"], safety=URGENT)
    screen = capsys.readouterr().out

    assert outcome == "safety_return"
    assert event_names(session) == [
        "safety_screened",
        "urgency_flag_presented",
        "break_glass_decided",
    ]
    assert calls == ["run_safety_screening"]
    assert "Potentia [" not in screen


def test_formulation_rejected(monkeypatch, tmp_path):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["n"])

    assert outcome == "cancelled"
    assert event_names(session) == [
        "safety_screened",
        "evidence_presented",
        "formulation_rejected",
    ]
    assert calls == ["run_safety_screening"]


def test_safety_unavailable(monkeypatch, tmp_path):
    outcome, session, calls = run_case(monkeypatch, tmp_path, [], safety=None)

    assert outcome == "failed"
    assert event_names(session) == ["safety_unavailable"]
    assert calls == ["run_safety_screening"]


def test_potentia_unavailable(monkeypatch, tmp_path):
    outcome, session, calls = run_case(monkeypatch, tmp_path, ["y"], potentia=None)

    assert outcome == "failed"
    assert event_names(session) == [
        "safety_screened",
        "evidence_presented",
        "formulation_confirmed",
        "potentia_response_unavailable",
    ]
    assert calls == ["run_safety_screening", "get_potentia_response"]
    