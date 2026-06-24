from __future__ import annotations

from pathlib import Path

import pytest

from python.scenario.pack import ScenarioPack, create_local_ai_pack, ScenarioMetadata


def test_scenario_pack_add_scenario() -> None:
    pack = ScenarioPack("scenarios/local_ai")
    pack.add_scenario(
        "test.json",
        "Test scenario",
        expected_executed_rate=0.95,
        expected_train_unit_actions=2,
    )

    assert pack.get_metadata("test.json") is not None
    meta = pack.get_metadata("test.json")
    assert meta.description == "Test scenario"
    assert meta.expected_executed_rate == 0.95


def test_scenario_pack_list_scenarios() -> None:
    pack = ScenarioPack("scenarios/local_ai")
    pack.add_scenario("a.json", "A", 0.9)
    pack.add_scenario("b.json", "B", 0.85)
    pack.add_scenario("c.json", "C", 0.95)

    scenarios = pack.list_scenarios()
    assert scenarios == ["a.json", "b.json", "c.json"]


def test_scenario_pack_export_import(tmp_path: Path) -> None:
    pack = ScenarioPack("scenarios/local_ai")
    pack.add_scenario("test.json", "Test", 0.95, expected_train_unit_actions=2)

    export_path = tmp_path / "metadata.json"
    pack.export_metadata(export_path)
    assert export_path.exists()

    pack2 = ScenarioPack("scenarios/local_ai")
    pack2.import_metadata(export_path)

    meta = pack2.get_metadata("test.json")
    assert meta is not None
    assert meta.description == "Test"
    assert meta.expected_train_unit_actions == 2


def test_create_local_ai_pack() -> None:
    pack = create_local_ai_pack()

    scenarios = pack.list_scenarios()
    assert "early_pressure.json" in scenarios
    assert "opening_balanced.json" in scenarios
    assert "counter_pressure.json" in scenarios

    # Verify expectations
    early_meta = pack.get_metadata("early_pressure.json")
    assert early_meta.expected_executed_rate == 1.0
    assert early_meta.expected_train_unit_actions == 1
