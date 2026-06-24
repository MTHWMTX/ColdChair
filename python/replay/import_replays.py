"""Import Warcraft III replay files (.w3g) into training datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click

from python.replay.w3g_parser import W3GParser


def parse_replay(replay_path: Path) -> list[dict]:
    """Parse a single replay file and extract game states."""
    parser = W3GParser()

    try:
        parsed = parser.parse(replay_path)
        samples = parser.to_game_state_samples(parsed)
        return samples
    except Exception as e:
        click.echo(f"⚠️  Failed to parse {replay_path.name}: {e}", err=True)
        return []


def import_replays_from_directory(
    replay_dir: Path, output_file: Optional[Path] = None, tag: str = ""
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
        click.echo(f"No replay files found in {replay_dir}")
        return 0

    click.echo(f"Found {len(replay_files)} replay file(s)")

    all_samples = []
    successful = 0

    for replay_file in sorted(replay_files):
        click.echo(f"→ Parsing {replay_file.name}...", nl=False)
        samples = parse_replay(replay_file)

        if samples:
            all_samples.extend(samples)
            successful += 1
            click.echo(f" ✓ ({len(samples)} states)")
        else:
            click.echo(" ✗ (no states)")

    if not all_samples:
        click.echo("No game states extracted from any replay files")
        return 0

    # Save to output file
    if output_file is None:
        output_file = replay_dir / "extracted_states.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(all_samples, f, indent=2)

    click.echo(
        f"\n✓ Extracted {len(all_samples)} game states from {successful} replay(s)"
    )
    click.echo(f"→ Saved to {output_file}")

    return len(all_samples)


@click.group()
def cli():
    """Warcraft III replay import tools."""
    pass


@cli.command()
@click.argument("replay_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output JSON file (default: same dir as input)",
)
def extract(replay_path: str, output: Optional[str]) -> None:
    """Extract game states from a single replay file."""
    input_path = Path(replay_path)
    output_path = Path(output) if output else input_path.with_suffix(".json")

    click.echo(f"Parsing replay: {input_path}")

    samples = parse_replay(input_path)

    if samples:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(samples, f, indent=2)
        click.echo(f"✓ Extracted {len(samples)} game states")
        click.echo(f"→ Saved to {output_path}")
    else:
        click.echo("Failed to extract any game states")


@cli.command()
@click.argument("replay_dir", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output JSON file (default: replay_dir/extracted_states.json)",
)
@click.option(
    "-t", "--tag", default="imported", help="Tag for dataset (default: 'imported')"
)
def batch(replay_dir: str, output: Optional[str], tag: str) -> None:
    """Batch import all replay files from a directory."""
    dir_path = Path(replay_dir)
    output_path = Path(output) if output else dir_path / "extracted_states.json"

    click.echo(f"Importing replays from: {dir_path}")

    try:
        import_replays_from_directory(dir_path, output_path, tag)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("dataset_file", type=click.Path(exists=True))
@click.option(
    "-d",
    "--dataset-id",
    required=True,
    help="Dataset ID for training system",
)
@click.option(
    "-n",
    "--name",
    default="Imported Dataset",
    help="Human-readable dataset name",
)
@click.option("-t", "--tags", default="imported", help="Comma-separated tags")
@click.option(
    "-s",
    "--samples-dir",
    type=click.Path(),
    default="datasets",
    help="Training datasets directory",
)
def register(
    dataset_file: str,
    dataset_id: str,
    name: str,
    tags: str,
    samples_dir: str,
) -> None:
    """Register an extracted dataset for training."""
    import subprocess

    dataset_path = Path(dataset_file)

    if not dataset_path.exists():
        click.echo(f"Dataset file not found: {dataset_path}")
        raise SystemExit(1)

    tag_list = [t.strip() for t in tags.split(",")]

    click.echo(f"Registering dataset: {name} (ID: {dataset_id})")
    click.echo(f"→ Source: {dataset_path}")

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
        click.echo(f"✓ Dataset registered successfully")
        if result.stdout:
            click.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to register dataset", err=True)
        if e.stderr:
            click.echo(e.stderr, err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
