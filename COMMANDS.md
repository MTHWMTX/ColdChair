# Command Reference

Concise reference for the common project commands and what they do.

## Replay ingestion and training

- `python scripts/import_and_train_replays.py`: Import replays from `replays/incoming`, register the dataset, and run training.
- `python scripts/import_and_train_replays.py --download-from-wc3info`: Download relevant replays from Warcraft3.Info first, then import, register, and train.
- `python scripts/import_and_train_replays.py --skip-training`: Import and register only, without training.
- `python scripts/import_and_train_replays.py --balance-dataset --group-mode subfolder_map --max-states-per-group 2000`: Build a balanced dataset before registration and training.
- `python scripts/download_wc3info_replays.py --dry-run`: Show which Warcraft3.Info replays would be downloaded without saving files.
- `python scripts/download_wc3info_replays.py --out-dir replays/incoming`: Download relevant Warcraft3.Info replays into the replay drop folder.
- `python scripts/backfill_wc3info_replays.py --skip-ssl-verification --replays-dir replays/incoming`: Move existing flat Warcraft3.Info replays into matchup/map folders and write metadata sidecars.
- `python -m python.replay.build_balanced_dataset --replays-dir replays/incoming --group-mode subfolder_map --out datasets/replays_balanced.json --max-states-per-group 2000 --manifest reports/replays_balanced_manifest.json`: Build a balanced replay dataset and emit a manifest.
- `python -m python.training.orchestrate register-dataset --dataset-id replays_balanced --name "Race-Balanced Replays" --samples datasets/replays_balanced.json --tags "replays,race_balanced"`: Register a dataset with the training system.
- `python -m python.training.orchestrate train --policy-version v1.0 --dataset-id replays_balanced --out reports/training_result_balanced.json`: Train a policy on a registered dataset.

## Offline validation

- `python -m python.policy.run_offline_eval --samples examples/sample_states.json --out reports/offline_eval.json`: Run offline policy evaluation on sample states.
- `python -m python.runtime.run_local_loop --samples examples/sample_states.json --out reports/local_loop_report.json`: Execute the local runtime loop in dry-run mode.
- `python -m python.runtime.run_self_play --samples examples/sample_states.json --ticks 80 --out reports/self_play_report.json`: Run deterministic offline self-play between two bot instances.
- `python -m python.runtime.run_self_play_tournament --samples examples/sample_states.json --rounds 20 --ticks 80 --bot-a-label candidate --bot-b-label baseline --out reports/self_play_tournament_report.json`: Run repeated self-play matches with Elo-style rating updates.
- `python -m python.runtime.run_scenarios --scenario-dir scenarios/local_ai --out reports/scenario_report.json`: Run the local scenario pack.
- `python -m python.runtime.generate_dashboard --out reports/system_dashboard.json`: Generate a combined system dashboard and readiness summary.

## Readiness and configuration

- `python -m python.bn_readiness.manage_readiness status`: Show Battle.net readiness status.
- `python -m python.bn_readiness.manage_readiness export --out reports/bn_readiness.json`: Export the Battle.net readiness report.
- `python -m python.config.run_experiment --config config.json --samples examples/sample_states.json --out reports/experiment_result.json --compare-to reports/baseline_result.json`: Run a parameterized configuration experiment.

## Notes

- Replay download defaults are safety-first: robots-aware, rate-limited, and filtered for recent high-level matches.
- The one-command replay flow assumes downloaded files land in `replays/incoming` unless you pass a different replay directory.
