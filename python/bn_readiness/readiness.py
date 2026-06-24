from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class ReadinessStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    READY = "ready"


@dataclass
class ReadinessCheck:
    name: str
    description: str
    status: ReadinessStatus = ReadinessStatus.NOT_STARTED
    severity: str = "info"  # info, warning, critical
    completed_by: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "severity": self.severity,
            "completed_by": self.completed_by,
            "notes": self.notes,
        }


@dataclass
class ReadinessPhase:
    """A phase of Battle.net readiness checks."""

    name: str
    description: str
    checks: dict[str, ReadinessCheck] = field(default_factory=dict)

    def add_check(self, check: ReadinessCheck) -> None:
        self.checks[check.name] = check

    def get_check(self, name: str) -> ReadinessCheck | None:
        return self.checks.get(name)

    def mark_complete(self, check_name: str, completed_by: str = "", notes: str = "") -> None:
        if check_name in self.checks:
            self.checks[check_name].status = ReadinessStatus.READY
            self.checks[check_name].completed_by = completed_by
            self.checks[check_name].notes = notes

    def progress(self) -> dict[str, int]:
        statuses = {}
        for check in self.checks.values():
            status = check.status.value
            statuses[status] = statuses.get(status, 0) + 1
        return statuses

    def is_phase_ready(self) -> bool:
        return all(check.status == ReadinessStatus.READY for check in self.checks.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "ready": self.is_phase_ready(),
            "progress": self.progress(),
            "checks": {name: check.to_dict() for name, check in self.checks.items()},
        }


class BattleNetReadiness:
    """Battle.net readiness checklist with multiple phases."""

    def __init__(self) -> None:
        self.phases: dict[str, ReadinessPhase] = {}
        self._init_default_phases()

    def _init_default_phases(self) -> None:
        """Initialize default Battle.net readiness phases."""
        # Phase 6: Supervised Local Loop Integration
        phase6 = ReadinessPhase(
            name="Phase 6: Supervised Local Loop",
            description="Local game loop integration with Battle.net account preparation",
        )
        phase6.add_check(
            ReadinessCheck(
                "local_loop_integration",
                "Local game loop fully integrated with perception and decision systems",
                severity="critical",
            )
        )
        phase6.add_check(
            ReadinessCheck(
                "supervised_dry_run",
                "Supervised dry-run framework complete with approval gates",
                severity="critical",
            )
        )
        phase6.add_check(
            ReadinessCheck(
                "account_preparation",
                "Dedicated disposable Battle.net account prepared and verified",
                severity="critical",
            )
        )
        phase6.add_check(
            ReadinessCheck(
                "safety_interlocks",
                "All safety interlocks and kill switches verified and tested",
                severity="critical",
            )
        )
        self.phases["phase6"] = phase6

        # Phase 7: Live Testing
        phase7 = ReadinessPhase(
            name="Phase 7: Live Testing",
            description="Limited live testing with continuous monitoring and safety checks",
        )
        phase7.add_check(
            ReadinessCheck(
                "live_test_approval",
                "Executive approval for limited live testing",
                severity="critical",
            )
        )
        phase7.add_check(
            ReadinessCheck(
                "monitoring_infrastructure",
                "Real-time monitoring and alerting infrastructure deployed",
                severity="critical",
            )
        )
        phase7.add_check(
            ReadinessCheck(
                "telemetry_collection",
                "Comprehensive telemetry collection for battle analysis",
                severity="critical",
            )
        )
        phase7.add_check(
            ReadinessCheck(
                "quick_shutdown",
                "Quick shutdown procedure documented and tested",
                severity="critical",
            )
        )
        self.phases["phase7"] = phase7

    def add_phase(self, phase: ReadinessPhase) -> None:
        self.phases[phase.name.lower().replace(" ", "_")] = phase

    def get_phase(self, phase_key: str) -> ReadinessPhase | None:
        return self.phases.get(phase_key)

    def list_phases(self) -> list[str]:
        return sorted(self.phases.keys())

    def overall_progress(self) -> dict[str, Any]:
        total_checks = sum(len(p.checks) for p in self.phases.values())
        ready_checks = sum(
            sum(1 for c in p.checks.values() if c.status == ReadinessStatus.READY)
            for p in self.phases.values()
        )

        return {
            "total_phases": len(self.phases),
            "phases_ready": sum(1 for p in self.phases.values() if p.is_phase_ready()),
            "total_checks": total_checks,
            "ready_checks": ready_checks,
            "overall_readiness_percent": (ready_checks / max(total_checks, 1)) * 100,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_progress": self.overall_progress(),
            "phases": {key: phase.to_dict() for key, phase in self.phases.items()},
        }
