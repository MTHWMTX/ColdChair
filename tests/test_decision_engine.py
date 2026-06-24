from python.policy.decision_engine import DecisionEngine


def test_decision_engine_returns_idle_without_units() -> None:
    engine = DecisionEngine()
    state = {
        "resources": {"gold": 0, "lumber": 0},
        "supply": {"used": 0, "cap": 0},
        "units": [],
    }

    actions = engine.decide(state)

    assert len(actions) == 1
    assert actions[0].type == "idle"


def test_decision_engine_prefers_training_when_resources_allow() -> None:
    engine = DecisionEngine()
    state = {
        "resources": {"gold": 200, "lumber": 60},
        "supply": {"used": 12, "cap": 20},
        "units": [{"owner": "self", "id": "u1", "type": "peasant", "hp": 220, "position": {"x": 1, "y": 1}}],
    }

    actions = engine.decide(state)

    assert actions[0].type == "train_unit"
