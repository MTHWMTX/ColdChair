from __future__ import annotations

from python.bn_readiness.readiness import BattleNetReadiness, ReadinessStatus


def test_battle_net_readiness_init() -> None:
    readiness = BattleNetReadiness()

    phases = readiness.list_phases()
    assert "phase6" in phases
    assert "phase7" in phases


def test_readiness_phase_add_check() -> None:
    readiness = BattleNetReadiness()
    phase6 = readiness.get_phase("phase6")

    assert phase6 is not None
    checks = phase6.checks
    assert "local_loop_integration" in checks
    assert "account_preparation" in checks


def test_readiness_phase_mark_complete() -> None:
    readiness = BattleNetReadiness()
    phase6 = readiness.get_phase("phase6")

    phase6.mark_complete("local_loop_integration", "test_user", "Completed successfully")

    check = phase6.get_check("local_loop_integration")
    assert check.status == ReadinessStatus.READY
    assert check.completed_by == "test_user"


def test_readiness_phase_is_ready() -> None:
    readiness = BattleNetReadiness()
    phase6 = readiness.get_phase("phase6")

    # Not ready initially
    assert not phase6.is_phase_ready()

    # Mark all checks complete
    for check_name in phase6.checks:
        phase6.mark_complete(check_name)

    # Now ready
    assert phase6.is_phase_ready()


def test_overall_progress() -> None:
    readiness = BattleNetReadiness()

    progress = readiness.overall_progress()
    assert progress["total_phases"] >= 2
    assert progress["total_checks"] >= 8
    assert progress["ready_checks"] == 0  # None ready yet
    assert progress["overall_readiness_percent"] == 0.0


def test_readiness_to_dict() -> None:
    readiness = BattleNetReadiness()

    data = readiness.to_dict()
    assert "overall_progress" in data
    assert "phases" in data
    assert data["overall_progress"]["total_phases"] >= 2
