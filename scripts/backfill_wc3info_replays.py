#!/usr/bin/env python
"""Backfill flat Warcraft3.Info replay files into matchup/map folders.

This script reads replay IDs from filenames like replay_123456_v2_00.w3g,
fetches the associated replay metadata from Warcraft3.Info, and moves the file
into the same matchup/map layout used by the downloader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import urllib.request
import urllib.parse
from pathlib import Path


DEFAULT_BASE_URL = "https://warcraft3.info/"
DEFAULT_USER_AGENT = "ColdChairReplayBot/0.1 (+local training prep; respectful crawler)"


def _slugify(value: object, fallback: str = "unknown") -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return text or fallback


def _normalize_race_name(value: object) -> str:
    text = str(value or "unknown").strip().lower()
    if not text:
        return "unknown"
    aliases = {
        "human": "human",
        "hum": "human",
        "orc": "orc",
        "nightelf": "nightelf",
        "night elf": "nightelf",
        "elf": "nightelf",
        "undead": "undead",
        "ud": "undead",
        "random": "random",
        "r": "random",
    }
    return aliases.get(text, _slugify(text))


def _sorted_matchup_label(players: object) -> str:
    races: list[str] = []
    if isinstance(players, list):
        ordered_players = sorted(
            [player for player in players if isinstance(player, dict)],
            key=lambda player: int(player.get("team", 0) or 0),
        )
        for player in ordered_players[:2]:
            race = player.get("race")
            if not race and isinstance(player.get("stats_player"), dict):
                race = player["stats_player"].get("main_race")
            races.append(_normalize_race_name(race))

    if len(races) < 2:
        return "unknown_vs_unknown"

    first, second = sorted(races[:2])
    return f"{first}_vs_{second}"


def _build_opener(user_agent: str, *, insecure_skip_ssl_verification: bool = False) -> urllib.request.OpenerDirector:
    if insecure_skip_ssl_verification:
        context = ssl._create_unverified_context()
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", user_agent)]
    return opener


def _file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_replay_ids(root: Path) -> list[int]:
    ids: list[int] = []
    for replay_file in sorted(root.glob("replay_*_v*.w3g")):
        if replay_file.parent != root:
            continue
        match = re.search(r"replay_(\d+)_v", replay_file.name)
        if match:
            ids.append(int(match.group(1)))
    return ids


def _target_path(out_dir: Path, replay: dict[str, object], major_version: int) -> Path:
    replay_id = replay.get("id")
    extension = str(replay.get("filetype") or "w3g").lower()
    version = str(replay.get("version", ""))
    patch_label = _format_patch_label(version, major_version)
    patch_token = patch_label.replace(".", "_")
    map_slug = _slugify(replay.get("map"), fallback="unknown_map")
    matchup_slug = _sorted_matchup_label(replay.get("players", []))
    filename = f"replay_{replay_id}_v{patch_token}.{extension}"
    return out_dir / matchup_slug / map_slug / filename


def _format_patch_label(version_code: str, major_version: int) -> str:
    code = version_code.strip()
    if not code:
        return f"{major_version}.??"
    parts = code.split(".")
    if len(parts) == 1 and parts[0].isdigit():
        return f"{major_version}.{parts[0].zfill(2)}"
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{major_version}.{int(parts[0]):02d}.{int(parts[1])}"
    return f"{major_version}.{code}"


def _fetch_replay_pages(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    *,
    page_limit: int,
    min_elo: int,
    filetype: str,
) -> dict[int, dict[str, object]]:
    endpoint = urllib.parse.urljoin(base_url, "/api/v1/replays")
    found: dict[int, dict[str, object]] = {}

    for page in range(1, page_limit + 1):
        payload = {
            "page": page,
            "filetype": filetype,
            "minimumElo": min_elo,
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with opener.open(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))

        rows = data.get("data", []) if isinstance(data, dict) else []
        if not rows:
            break

        for row in rows:
            if isinstance(row, dict) and row.get("id") is not None:
                found[int(row["id"])] = row

        last_page = int(data.get("last_page", page)) if isinstance(data, dict) else page
        if page >= last_page:
            break

    return found


def _fetch_replay_by_id(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    replay_id: int,
) -> dict[str, object] | None:
    endpoint = urllib.parse.urljoin(base_url, f"/api/v1/replays/{replay_id}")
    with opener.open(endpoint, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    return payload if isinstance(payload, dict) else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill flat Warcraft3.Info replay files")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--replays-dir", default="replays/incoming")
    parser.add_argument("--major-version", type=int, default=2)
    parser.add_argument("--min-elo", type=int, default=2400)
    parser.add_argument("--filetype", choices=["w3g", "nwg"], default="w3g")
    parser.add_argument("--page-limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-ssl-verification", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.replays_dir)
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    local_ids = _load_replay_ids(root)
    if not local_ids:
        print(f"No flat replay files found in {root}")
        return 0

    opener = _build_opener(
        DEFAULT_USER_AGENT,
        insecure_skip_ssl_verification=args.skip_ssl_verification,
    )

    metadata_by_id = _fetch_replay_pages(
        opener,
        args.base_url,
        page_limit=args.page_limit,
        min_elo=args.min_elo,
        filetype=args.filetype,
    )

    moved = 0
    skipped = 0
    unresolved: list[int] = []

    for replay_id in local_ids:
        replay = metadata_by_id.get(replay_id)
        if replay is None:
            replay = _fetch_replay_by_id(opener, args.base_url, replay_id)
        if not replay:
            unresolved.append(replay_id)
            continue

        source_candidates = sorted(root.glob(f"replay_{replay_id}_v*.w3g"))
        if not source_candidates:
            unresolved.append(replay_id)
            continue

        source = source_candidates[0]
        target = _target_path(root, replay, args.major_version)
        sidecar = Path(str(target) + ".meta.json")

        if target.exists():
            if _file_hash(source) == _file_hash(target):
                source.unlink()
                skipped += 1
                continue
            print(f"[warn] target already exists with different content: {target}")
            skipped += 1
            continue

        print(f"[move] {source} -> {target}")
        if args.dry_run:
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)

        sidecar_payload = {
            "replay_id": replay.get("id"),
            "map": replay.get("map"),
            "map_alias": replay.get("map_alias"),
            "matchup": _sorted_matchup_label(replay.get("players", [])),
            "version": replay.get("version"),
            "patch_label": _format_patch_label(str(replay.get("version", "")), args.major_version),
            "created_at": replay.get("created_at"),
            "filetype": replay.get("filetype"),
            "source_url": urllib.parse.urljoin(args.base_url, f"/api/v1/replays/{replay_id}/download"),
            "players": replay.get("players", []),
        }
        sidecar.write_text(json.dumps(sidecar_payload, indent=2), encoding="utf-8")
        moved += 1

    if unresolved:
        print(f"[warn] unresolved replay ids: {', '.join(map(str, unresolved))}")

    print(f"[result] moved={moved} skipped={skipped} unresolved={len(unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())