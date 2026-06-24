from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from python.policy.decision_engine import ActionIntent
from python.runtime.game_adapter import SupervisedGameAdapter
from python.runtime.targeting import CommandEnricher


@dataclass
class ExecutionResult:
    status: str
    command: dict
    dry_run: bool
    reason: str = ""


class IntentExecutor:
    """Maps action intents to runtime commands with optional telemetry hooks."""

    def __init__(
        self,
        *,
        dry_run: bool = True,
        telemetry_hook: Callable[[ExecutionResult], None] | None = None,
        adapter: SupervisedGameAdapter | None = None,
        command_enricher: CommandEnricher | None = None,
    ) -> None:
        self.dry_run = dry_run
        self.telemetry_hook = telemetry_hook
        self.adapter = adapter
        self.command_enricher = command_enricher

    def execute(self, intent: ActionIntent, state: dict[str, Any] | None = None) -> ExecutionResult:
        command = self._command_for_intent(intent)
        if command is None:
            result = ExecutionResult(
                status="unsupported",
                command={"type": intent.type},
                dry_run=self.dry_run,
                reason="unsupported_intent",
            )
            self._emit(result)
            return result

        if self.command_enricher is not None:
            command = self.command_enricher.enrich_command(command, intent, state)

        if self.dry_run:
            # Runtime command dispatch remains dry-run by default in MVP.
            result = ExecutionResult(status="executed", command=command, dry_run=True)
            self._emit(result)
            return result

        if self.adapter is None:
            result = ExecutionResult(
                status="blocked",
                command=command,
                dry_run=False,
                reason="live_execution_requires_adapter",
            )
            self._emit(result)
            return result

        dispatch = self.adapter.dispatch(command)
        result = ExecutionResult(
            status=dispatch.status,
            command=command,
            dry_run=False,
            reason=dispatch.reason,
        )
        self._emit(result)
        return result

    def _emit(self, result: ExecutionResult) -> None:
        if self.telemetry_hook is not None:
            self.telemetry_hook(result)

    def _command_for_intent(self, intent: ActionIntent) -> dict | None:
        if intent.type == "train_unit":
            return {"op": "key_press", "key": "T"}

        if intent.type == "gather_resources":
            return {"op": "right_click_resource"}

        if intent.type == "attack_move":
            if not intent.position:
                return None
            return {
                "op": "attack_move",
                "x": float(intent.position["x"]),
                "y": float(intent.position["y"]),
            }

        if intent.type == "idle":
            return {"op": "noop"}

        return None
