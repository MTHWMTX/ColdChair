# Architecture

## High-Level Flow
1. Replay ingestion or perception input produces normalized game state.
2. Policy consumes state and emits intent actions.
3. Runtime layer translates intents into executable controls.
4. Telemetry records state, intent, and execution outcomes.

## Modules
- python/replay: Replay parsing and state extraction.
- python/replay/sample_loader.py: Normalized state sample loading from JSON and JSONL.
- python/replay/extract_timeline.py: Replay input to normalized JSONL state timeline export.
- python/policy: Baseline rule policy and offline evaluator.
- python/policy/run_offline_eval.py: CLI entry point for offline policy scoring reports.
- python/policy/benchmark_eval.py: Evaluation latency benchmark and metadata report.
- python/perception: Frame capture and confidence scoring stubs.
- python/runtime/action_queue.py: Safety-aware queue with kill switch, focus check, and rate limits.
- python/runtime/executor.py: Intent-to-command mapping with dry-run telemetry hooks.
- python/runtime/local_loop.py: Supervised local decision-to-action loop runner.
- python/runtime/run_local_loop.py: CLI entry point for local loop report generation.
- python/runtime/run_scenarios.py: Scenario-pack regression runner for local loop outcomes.
- contracts: Shared schemas used by Python and C# components.
- contracts/action_intent.schema.json: Intent schema for runtime command payloads.
- python/contracts/validator.py: Shared JSON-schema validation for game state and action intents.
- dotnet/runtime: Runtime orchestration and action queue skeleton.
- tests: Unit and integration tests.

## Interface Contract
- Inputs and outputs are represented as JSON using contracts/game_state.schema.json.
- Policy output follows a simple action intent shape:
  - type: string
  - target_id: optional string
  - position: optional x and y
  - priority: integer

## Operational Mode
- Default mode is offline.
- Any future online mode must be user-triggered and supervised.

## Drift Reporting
- Scenario regression output includes per-scenario executed-rate metrics.
- Optional baseline comparison reports pass/fail drift against configurable threshold.
