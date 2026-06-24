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
4. Phase 4: Vision and control foundations.
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

## Git Workflow
- Trunk-based with short-lived milestone branches.
- Push once per completed phase milestone.
- Conventional commits: chore, feat, test, docs.
