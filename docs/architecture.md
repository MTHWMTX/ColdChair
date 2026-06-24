# Architecture

## High-Level Flow
1. Replay ingestion or perception input produces normalized game state.
2. Policy consumes state and emits intent actions.
3. Runtime layer translates intents into executable controls.
4. Telemetry records state, intent, and execution outcomes.

## Modules
- python/replay: Replay parsing and state extraction.
- python/replay/sample_loader.py: Normalized state sample loading from JSON and JSONL.
- python/policy: Baseline rule policy and offline evaluator.
- python/policy/run_offline_eval.py: CLI entry point for offline policy scoring reports.
- python/perception: Frame capture and confidence scoring stubs.
- contracts: Shared schemas used by Python and C# components.
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
