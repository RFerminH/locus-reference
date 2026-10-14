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


def test_discrepancy_shows_potentia_before_analysis(monkeypatch, tmp_path, capsys):
    fake_results= {
        "run_safety_screening": SafetyScreening(result=SafetyScreeningResult.NONE),
        "get_potentia_response": PotentiaResponse(potentia_formulation="Vestibular migraine", rationale="Episodic vertigo with headache"),
        "match_formulations": MatchingOutcome(result=MatchingResult.DIVERGENCE),
        "get_evidentiary_analysis": SimpleNamespace(model_dump=lambda mode: {"decision_fork": "test"}),
    }
    monkeypatch.setattr(clinical_pipeline, "call_with_standby", lambda func, *args: fake_results[func.__name__])
    monkeypatch.setattr(clinical_pipeline, "render_analysis", lambda analysis: "ANALYSIS TEXT")

    answers = iter(["y", "My explanation.", "Keep my formulation"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    session = start_session(tmp_path)
    case = StructuredInput(evidence_packet="Episodic vertigo.", potestas_formulation="Meniere disease.")

    outcome = clinical_pipeline.run_pipeline(case, None, session)

    events = [event["event"] for event in session["events"]]
    screen = capsys.readouterr().out

    assert outcome == "completed"
    assert events == [
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
    assert "Potentia [Formulator], formulation: Vestibular migraine" in screen
    assert screen.index("Vestibular migraine") < screen.index("ANALYSIS TEXT")

