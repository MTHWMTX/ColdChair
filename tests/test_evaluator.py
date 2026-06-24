from python.policy.evaluator import OfflinePolicyEvaluator


def test_evaluator_returns_zeroes_for_empty_samples() -> None:
    evaluator = OfflinePolicyEvaluator()

    summary = evaluator.evaluate([])

    assert summary.total_states == 0
    assert summary.train_unit_rate == 0.0
    assert summary.attack_move_rate == 0.0
    assert summary.gather_rate == 0.0


def test_evaluator_computes_intent_rates() -> None:
    evaluator = OfflinePolicyEvaluator()
    states = [
        {
            "resources": {"gold": 200, "lumber": 60},
            "supply": {"used": 10, "cap": 20},
            "units": [{"owner": "self", "id": "a", "type": "peasant", "hp": 100, "position": {"x": 1, "y": 1}}],
        },
        {
            "resources": {"gold": 20, "lumber": 0},
            "supply": {"used": 9, "cap": 20},
            "units": [{"owner": "self", "id": "b", "type": "footman", "hp": 300, "position": {"x": 3, "y": 4}}],
        },
    ]

    summary = evaluator.evaluate(states)

    assert summary.total_states == 2
    assert summary.train_unit_rate == 0.5
    assert summary.attack_move_rate == 0.0
    assert summary.gather_rate == 0.5


def test_evaluator_gate_passes_with_reasonable_thresholds() -> None:
    evaluator = OfflinePolicyEvaluator()
    states = [
        {
            "resources": {"gold": 200, "lumber": 60},
            "supply": {"used": 10, "cap": 20},
            "units": [{"owner": "self", "id": "a", "type": "peasant", "hp": 100, "position": {"x": 1, "y": 1}}],
        },
        {
            "resources": {"gold": 20, "lumber": 0},
            "supply": {"used": 9, "cap": 20},
            "units": [{"owner": "self", "id": "b", "type": "footman", "hp": 300, "position": {"x": 3, "y": 4}}],
        },
    ]

    summary = evaluator.evaluate(states)
    gate = evaluator.evaluate_gate(summary, min_states=2, min_train_rate=0.4, min_gather_rate=0.4)

    assert gate.passed is True
    assert gate.reasons == []


def test_evaluator_gate_fails_with_strict_thresholds() -> None:
    evaluator = OfflinePolicyEvaluator()
    states = [
        {
            "resources": {"gold": 200, "lumber": 60},
            "supply": {"used": 10, "cap": 20},
            "units": [{"owner": "self", "id": "a", "type": "peasant", "hp": 100, "position": {"x": 1, "y": 1}}],
        },
        {
            "resources": {"gold": 20, "lumber": 0},
            "supply": {"used": 9, "cap": 20},
            "units": [{"owner": "self", "id": "b", "type": "footman", "hp": 300, "position": {"x": 3, "y": 4}}],
        },
    ]

    summary = evaluator.evaluate(states)
    gate = evaluator.evaluate_gate(summary, min_states=3, min_train_rate=0.8, min_gather_rate=0.8)

    assert gate.passed is False
    assert len(gate.reasons) == 3
