"""Import Warcraft III replay files (.w3g) into training datasets."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from python.replay.w3g_parser import W3GParser


def parse_replay(replay_path: Path, verbose: bool = False) -> list[dict]:
    """Parse a single replay file and extract game states."""
    parser = W3GParser()

    try:
        parsed = parser.parse(replay_path)
        samples = parser.to_game_state_samples(parsed)
        return samples
    except Exception as e:
        if verbose:
            print(f"⚠️  Failed to parse {replay_path.name}: {e}", file=sys.stderr)
        return []


def import_replays_from_directory(
    replay_dir: Path, output_file: Optional[Path] = None, tag: str = "", verbose: bool = True
) -> int:
    """Import all replay files from a directory."""
    replay_dir = Path(replay_dir)
    if not replay_dir.is_dir():
        raise ValueError(f"Not a directory: {replay_dir}")

    # Find all .w3g and .json replay files
    replay_files = list(replay_dir.glob("**/*.w3g")) + list(
        replay_dir.glob("**/*.json")
    )
    replay_files = [f for f in replay_files if f.is_file()]

    if not replay_files:
        if verbose:
            print(f"No replay files found in {replay_dir}")
        return 0

    if verbose:
        print(f"Found {len(replay_files)} replay file(s)")

    all_samples = []
    successful = 0

    for replay_file in sorted(replay_files):
        if verbose:
            print(f"→ Parsing {replay_file.name}...", end="", flush=True)
        samples = parse_replay(replay_file, verbose=verbose)

        if samples:
            all_samples.extend(samples)
            successful += 1
            if verbose:
                print(f" ✓ ({len(samples)} states)")
        else:
            if verbose:
                print(" ✗ (no states)")

    if not all_samples:
        if verbose:
            print("No game states extracted from any replay files")
        return 0

    # Save to output file
    if output_file is None:
        output_file = replay_dir / "extracted_states.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(all_samples, f, indent=2)

    if verbose:
        print(f"\n✓ Extracted {len(all_samples)} game states from {successful} replay(s)")
        print(f"→ Saved to {output_file}")

    return len(all_samples)


def extract_cmd(replay_path: str, output: Optional[str]) -> None:
    """Extract game states from a single replay file."""
    input_path = Path(replay_path)
    output_path = Path(output) if output else input_path.with_suffix(".json")

    print(f"Parsing replay: {input_path}")

    samples = parse_replay(input_path, verbose=True)

    if samples:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(samples, f, indent=2)
        print(f"✓ Extracted {len(samples)} game states")
        print(f"→ Saved to {output_path}")
    else:
        print("Failed to extract any game states")


def batch_cmd(replay_dir: str, output: Optional[str], tag: str) -> None:
    """Batch import all replay files from a directory."""
    dir_path = Path(replay_dir)
    output_path = Path(output) if output else dir_path / "extracted_states.json"

    print(f"Importing replays from: {dir_path}")

    try:
        import_replays_from_directory(dir_path, output_path, tag, verbose=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_cmd(
    dataset_file: str,
    dataset_id: str,
    name: str,
    tags: str,
    samples_dir: str,
) -> None:
    """Register an extracted dataset for training."""
    dataset_path = Path(dataset_file)

    if not dataset_path.exists():
        print(f"Dataset file not found: {dataset_path}")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",")]

    print(f"Registering dataset: {name} (ID: {dataset_id})")
    print(f"→ Source: {dataset_path}")

    # Use training orchestrator to register
    cmd = [
        "python",
        "-m",
        "python.training.orchestrate",
        "register-dataset",
        "--dataset-id",
        dataset_id,
        "--name",
        name,
        "--description",
        f"Dataset from {dataset_path.name}",
        "--samples",
        str(dataset_path),
        "--tags",
        ",".join(tag_list),
        "--samples-dir",
        samples_dir,
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Dataset registered successfully")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to register dataset", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """CLI for replay import tools."""
    parser = argparse.ArgumentParser(description="Warcraft III replay import tools")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract from single replay")
    extract_parser.add_argument("replay_path", type=str, help="Path to replay file")
    extract_parser.add_argument("-o", "--output", type=str, help="Output JSON file")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch import from directory")
    batch_parser.add_argument("replay_dir", type=str, help="Directory with replays")
    batch_parser.add_argument("-o", "--output", type=str, help="Output JSON file")
    batch_parser.add_argument("-t", "--tag", default="imported", help="Dataset tag")

    # Register command
    register_parser = subparsers.add_parser("register", help="Register dataset")
    register_parser.add_argument("dataset_file", type=str, help="Dataset JSON file")
    register_parser.add_argument("-d", "--dataset-id", required=True, help="Dataset ID")
    register_parser.add_argument("-n", "--name", default="Imported Dataset", help="Dataset name")
    register_parser.add_argument("-t", "--tags", default="imported", help="Tags")
    register_parser.add_argument("-s", "--samples-dir", default="datasets", help="Datasets directory")

    args = parser.parse_args()

    if args.command == "extract":
        extract_cmd(args.replay_path, args.output)
    elif args.command == "batch":
        batch_cmd(args.replay_dir, args.output, args.tag)
    elif args.command == "register":
        register_cmd(args.dataset_file, args.dataset_id, args.name, args.tags, args.samples_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
