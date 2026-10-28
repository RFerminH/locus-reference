from shared import call_with_standby

def test_retry_accepted_calls_again_and_returns_result(monkeypatch):
    results = iter([None, "RESULT"])
    received = []

    def fake_component(*args):
        received.append(args)
        return next(results)

    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    outcome = call_with_standby(fake_component, "Episodic vertigo.", None)

    assert outcome == "RESULT"
    assert received == [("Episodic vertigo.", None), ("Episodic vertigo.", None)]


def test_retry_declined_returns_none_without_calling_again(monkeypatch):
    results = iter([None, "RESULT"])
    received= []

    def fake_component(*args):
        received.append(args)
        return next(results)

    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    outcome = call_with_standby(fake_component, "Episodic vertigo.", None)

    assert outcome is None
    assert received == [("Episodic vertigo.", None )]