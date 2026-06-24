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

## Git Workflow
- Trunk-based with short-lived milestone branches.
- Push once per completed phase milestone.
- Conventional commits: chore, feat, test, docs.
