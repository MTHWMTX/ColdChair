# ColdChair

Safety-first Warcraft III: The Frozen Throne bot foundation.

## Scope
- 1v1 melee focus.
- Replay-first development.
- Offline and local AI validation before any online considerations.
- Hybrid stack: Python for replay and perception modules, C# for runtime orchestration.

## Non-Goals
- No anti-cheat bypass or evasion features.
- No process injection or memory editing.
- No unattended live matchmaking automation.

## Milestones
1. Phase 1: Project definition and guardrails.
2. Phase 2: Core domain model and replay pipeline.
3. Phase 3: Offline policy evaluation.
4. Phase 4: Vision and control foundations, including safety-aware action queue.
5. Phase 5: Local end-to-end loop versus AI.
6. Phase 6: Battle.net readiness checks without matchmaking automation.

## Quick Start
1. Create a Python virtual environment.
2. Install dependencies from requirements.txt.
3. Run tests with pytest.

## Offline Evaluation
1. Prepare state samples in JSON or JSONL format.
2. Run:

```bash
python -m python.policy.run_offline_eval --samples examples/sample_states.json --out reports/offline_eval.json
```

3. Review the generated report file in reports.

## Replay Extraction
1. Prepare a placeholder replay JSON file in the current format used by examples/sample_replay.json.
2. Run:

```bash
python -m python.replay.extract_timeline --replay examples/sample_replay.json --out reports/replay_states.jsonl
```

3. Feed extracted output into offline evaluation:

```bash
python -m python.policy.run_offline_eval --samples reports/replay_states.jsonl --out reports/offline_eval_from_replay.json
```

## Benchmark
Run evaluation latency benchmark:

```bash
python -m python.policy.benchmark_eval --samples examples/sample_states.json --runs 20 --out reports/eval_benchmark.json
```

## Supervised Local Loop
Run policy to runtime queue execution over state samples:

```bash
python -m python.runtime.run_local_loop --samples examples/sample_states.json --out reports/local_loop_report.json
```

Use --window-inactive to verify safety blocking behavior.
Use --live-execution to disable dry-run telemetry mode.

For supervised local in-game testing (Windows):

```bash
python -m python.runtime.run_local_loop \
	--samples examples/sample_states.json \
	--out reports/local_loop_live_report.json \
	--live-execution \
	--allow-live-input \
	--target-profile examples/live_target_profile.json \
	--window-title-contains "Warcraft III" \
	--confirm-each-action
```

Safety notes:
- Live input is blocked unless --allow-live-input is provided.
- Active window title must match --window-title-contains (unless --no-window-check is set).
- Use --target-profile to map abstract/world coordinates to concrete screen coordinates.
- In MVP, full perception is still pending; profile/resource_nodes provide target coordinates.

## Scenario Pack Regression
Run all scenarios in the local scenario pack:

```bash
python -m python.runtime.run_scenarios --scenario-dir scenarios/local_ai --out reports/scenario_report.json
```

Compare against a previous baseline report and fail drift over threshold:

```bash
python -m python.runtime.run_scenarios --scenario-dir scenarios/local_ai --baseline reports/scenario_report_baseline.json --max-drift 0.15 --out reports/scenario_report.json
```

Create or refresh a baseline snapshot:

```bash
python -m python.runtime.create_scenario_baseline --scenario-dir scenarios/local_ai --out scenarios/local_ai/baseline_report.json
```

Run strict drift gate and return non-zero on failures:

```bash
python -m python.runtime.run_scenarios --scenario-dir scenarios/local_ai --baseline scenarios/local_ai/baseline_report.json --require-baseline-match --max-drift 0.0 --fail-on-drift --out reports/scenario_report_gated.json
```

## Training Framework
Start iterative policy improvement with the training orchestrator:

```bash
# Initialize a policy version
python -m python.training.orchestrate init-policy --version v1.0 --description "Initial baseline policy"

# Register training dataset
python -m python.training.orchestrate register-dataset --dataset-id ds1 --name "Training Set" --samples data/replays.json --tags "training,baseline"

# Run training on dataset
python -m python.training.orchestrate train --policy-version v1.0 --dataset-id ds1 --out reports/training_result.json

# Check training status
python -m python.training.orchestrate status
```

The framework tracks:
- Multiple policy versions with metadata
- Training datasets with tags and sample counts
- Training runs and metrics
- Best performing version across all runs

One-command replay import + registration + training:

```bash
python scripts/import_and_train_replays.py
```

Default replay drop folder:
- replays/incoming

Useful options:
- --skip-training (import/register only)
- --policy-version v1.1
- --train-dataset-id pro_combined

## System Dashboard\nView comprehensive system health and readiness metrics:\n\n```bash\n# Generate system dashboard with all aggregated metrics\npython -m python.runtime.generate_dashboard --out reports/system_dashboard.json\n```\n\nThe dashboard aggregates:\n- Pipeline health and report availability\n- Experiment results and validation gates\n- Scenario regression status\n- Battle.net readiness checklist progress\n- System-wide alerts and issues\n\n## Battle.net Readiness Management
Track readiness for Battle.net integration with comprehensive checklists:

```bash
# Check readiness status
python -m python.bn_readiness.manage_readiness status

# Mark a check as complete
python -m python.bn_readiness.manage_readiness mark-ready --phase phase6 --check local_loop_integration --completed-by user@email.com --notes "Completed on date"

# Export readiness report
python -m python.bn_readiness.manage_readiness export --out reports/bn_readiness.json
```

## Configuration Management
Manage pipeline configurations and run parameterized experiments:

```bash
# Create a configuration
python -c "from python.config.pipeline_config import create_default_config; import json; from pathlib import Path; config = create_default_config(); Path('config.json').write_text(json.dumps(config.to_dict()))"

# Run experiment with configuration
python -m python.config.run_experiment --config config.json --samples examples/sample_states.json --out reports/experiment_result.json --compare-to reports/baseline_result.json
```

## End-to-End Pipeline
Run a complete pipeline from state loading through execution with telemetry:

```bash
python -m python.runtime.run_e2e_pipeline --samples examples/sample_states.json --out reports/e2e_report.json --telemetry reports/e2e_telemetry.json
```

## Offline Self-Play
Run two bot instances against each other in a deterministic offline arena:

```bash
python -m python.runtime.run_self_play --samples examples/sample_states.json --ticks 80 --out reports/self_play_report.json
```

Alternative seed format:
- Use --initial-state with a shared-state JSON object containing players.bot_a and players.bot_b.

Self-play report includes:
- Winner (bot_a, bot_b, draw)
- Per-tick intent/execution logs for both bots
- Resource/unit progression signals for training analysis

## Ranked Self-Play Tournament
Run repeated side-swapped self-play matches with Elo-style rating updates:

```bash
python -m python.runtime.run_self_play_tournament --samples examples/sample_states.json --rounds 20 --ticks 80 --bot-a-label candidate --bot-b-label baseline --out reports/self_play_tournament_report.json
```

Tournament report includes:
- Total games (2 per round)
- Wins/losses/draws per label
- Elo ratings for candidate and baseline
- Per-game logs with side assignment and rating progression

## Health Report
Generate a system health report aggregating all pipeline artifacts:

```bash
python -m python.runtime.generate_health_report --reports-dir reports --out reports/health_report.json
```

## Contract Validation
- State samples are validated against contracts/game_state.schema.json at load time.
- Action intents are validated against contracts/action_intent.schema.json before queueing.
- C# runtime parity skeleton validates the same contracts:

```bash
dotnet build dotnet/runtime/ColdChair.Runtime.csproj -c Release
dotnet run --project dotnet/runtime/ColdChair.Runtime.csproj -- validate-game-state --file examples/sample_game_state.json
dotnet run --project dotnet/runtime/ColdChair.Runtime.csproj -- validate-action-intent --file examples/sample_action_intent.json
```

## Git Workflow
- Trunk-based with short-lived milestone branches.
- Push once per completed phase milestone.
- Conventional commits: chore, feat, test, docs.
