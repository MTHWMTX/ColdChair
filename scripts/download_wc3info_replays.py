"""Polite Warcraft3.Info replay link downloader.

This script is intentionally conservative to avoid overloading the site:
- Honors robots.txt before fetching pages.
- Sleeps between requests with jitter.
- Uses a low default page cap.
- Retries with exponential backoff on transient failures.

It discovers article pages from the front page and downloads linked .w3g files.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from datetime import datetime, timedelta, timezone
import urllib.error
import urllib.parse
import urllib.request
import ssl
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.robotparser import RobotFileParser

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


def _replay_sidecar_path(target: Path) -> Path:
    return Path(str(target) + ".meta.json")


class LinkParser(HTMLParser):
    """Simple HTML link extractor for href attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


def _build_opener(
    user_agent: str,
    *,
    insecure_skip_ssl_verification: bool = False,
) -> urllib.request.OpenerDirector:
    if insecure_skip_ssl_verification:
        context = ssl._create_unverified_context()
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", user_agent)]
    return opener


def _build_api_target_path(out_dir: Path, replay: dict[str, object], major_version: int) -> Path:
    replay_id = replay.get("id")
    extension = str(replay.get("filetype") or "w3g").lower()
    patch_label = _format_patch_label(str(replay.get("version", "")), major_version)
    patch_token = patch_label.replace(".", "_")
    map_slug = _slugify(replay.get("map"), fallback="unknown_map")
    matchup_slug = _sorted_matchup_label(replay.get("players", []))
    filename = f"replay_{replay_id}_v{patch_token}.{extension}"
    return out_dir / matchup_slug / map_slug / filename


def _write_replay_sidecar(target: Path, replay: dict[str, object], *, patch_label: str, source_url: str) -> None:
    sidecar = _replay_sidecar_path(target)
    payload = {
        "replay_id": replay.get("id"),
        "map": replay.get("map"),
        "map_alias": replay.get("map_alias"),
        "matchup": _sorted_matchup_label(replay.get("players", [])),
        "version": replay.get("version"),
        "patch_label": patch_label,
        "created_at": replay.get("created_at"),
        "filetype": replay.get("filetype"),
        "source_url": source_url,
        "players": replay.get("players", []),
    }
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _fetch_text(
    opener: urllib.request.OpenerDirector,
    url: str,
    timeout_s: float,
    retries: int,
    backoff_s: float,
) -> str:
    """Fetch UTF-8-ish text with retries for transient HTTP errors."""
    delay = backoff_s
    for attempt in range(retries + 1):
        try:
            with opener.open(url, timeout=timeout_s) as response:
                content_type = response.headers.get("Content-Type", "")
                charset = "utf-8"
                if "charset=" in content_type:
                    charset = content_type.split("charset=")[-1].split(";")[0].strip()
                return response.read().decode(charset, errors="replace")
        except urllib.error.HTTPError as exc:
            # Retry only 5xx or 429; 4xx usually means permanent for this URL.
            if attempt < retries and (500 <= exc.code <= 599 or exc.code == 429):
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise


class PoliteCrawler:
    def __init__(
        self,
        base_url: str,
        user_agent: str,
        min_delay_s: float,
        max_jitter_s: float,
        timeout_s: float,
        retries: int,
        backoff_s: float,
        insecure_skip_ssl_verification: bool = False,
    ) -> None:
        self.base_url = base_url
        self.user_agent = user_agent
        self.min_delay_s = min_delay_s
        self.max_jitter_s = max_jitter_s
        self.timeout_s = timeout_s
        self.retries = retries
        self.backoff_s = backoff_s
        self.insecure_skip_ssl_verification = insecure_skip_ssl_verification
        self._last_request_ts = 0.0
        self.opener = _build_opener(
            user_agent,
            insecure_skip_ssl_verification=insecure_skip_ssl_verification,
        )
        self.robots = RobotFileParser()
        self.robots.set_url(urllib.parse.urljoin(base_url, "robots.txt"))
        try:
            robots_txt = _fetch_text(
                opener=self.opener,
                url=urllib.parse.urljoin(base_url, "robots.txt"),
                timeout_s=self.timeout_s,
                retries=self.retries,
                backoff_s=self.backoff_s,
            )
            self.robots.parse(robots_txt.splitlines())
        except Exception:
            # If robots.txt cannot be fetched, fall back to allowing checks to proceed.
            self.robots.parse(["User-agent: *", "Allow: /"])

    def _sleep_if_needed(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        required = self.min_delay_s + random.uniform(0.0, self.max_jitter_s)
        if elapsed < required:
            time.sleep(required - elapsed)

    def can_fetch(self, url: str) -> bool:
        return self.robots.can_fetch(self.user_agent, url)

    def fetch_html(self, url: str) -> str:
        if not self.can_fetch(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")
        self._sleep_if_needed()
        html = _fetch_text(
            opener=self.opener,
            url=url,
            timeout_s=self.timeout_s,
            retries=self.retries,
            backoff_s=self.backoff_s,
        )
        self._last_request_ts = time.monotonic()
        return html

    def fetch_json(self, url: str) -> object:
        payload = self.fetch_html(url)
        return json.loads(payload)

    def post_json(self, url: str, payload: dict[str, object]) -> object:
        if not self.can_fetch(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")
        self._sleep_if_needed()
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        delay = self.backoff_s
        response_text = ""
        for attempt in range(self.retries + 1):
            try:
                with self.opener.open(req, timeout=self.timeout_s) as response:
                    content_type = response.headers.get("Content-Type", "")
                    charset = "utf-8"
                    if "charset=" in content_type:
                        charset = content_type.split("charset=")[-1].split(";")[0].strip()
                    response_text = response.read().decode(charset, errors="replace")
                    break
            except urllib.error.HTTPError as exc:
                if attempt < self.retries and (500 <= exc.code <= 599 or exc.code == 429):
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
            except urllib.error.URLError:
                if attempt < self.retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
        self._last_request_ts = time.monotonic()
        return json.loads(response_text)

    def download_file(self, url: str, destination: Path) -> None:
        if not self.can_fetch(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")
        self._sleep_if_needed()
        with self.opener.open(url, timeout=self.timeout_s) as response:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.read())
        self._last_request_ts = time.monotonic()


def _extract_links(html: str, base_url: str) -> list[str]:
    parser = LinkParser()
    parser.feed(html)
    seen: set[str] = set()
    links: list[str] = []
    for href in parser.links:
        absolute = urllib.parse.urljoin(base_url, href)
        if absolute not in seen:
            seen.add(absolute)
            links.append(absolute)
    return links


def _article_urls(links: Iterable[str], base_url: str) -> list[str]:
    pattern = re.compile(
        r"^" + re.escape(base_url.rstrip("/")) + r"/articles/\d+(?:/[^/?#]+)?/?$"
    )
    articles = sorted({u for u in links if pattern.match(u)})
    return articles


def _article_urls_from_api(crawler: PoliteCrawler, base_url: str, max_pages: int) -> list[str]:
    """Discover article routes from the public API used by the frontend SPA."""
    api_base = urllib.parse.urljoin(base_url, "/api/v1/articles")
    collected: list[str] = []
    page = 1

    while page <= max_pages:
        api_url = f"{api_base}?page={page}"
        if not crawler.can_fetch(api_url):
            print(f"[skip] Blocked by robots.txt: {api_url}")
            break

        try:
            payload = crawler.fetch_html(api_url)
            data = json.loads(payload)
        except Exception as exc:  # pragma: no cover - defensive for live web variability.
            print(f"[warn] failed to fetch article API page {page}: {exc}")
            break

        records = data.get("data", []) if isinstance(data, dict) else []
        if not records:
            break

        for record in records:
            if not isinstance(record, dict):
                continue
            article_id = record.get("id")
            slug = record.get("slug")
            if article_id is None:
                continue
            if slug:
                article_url = urllib.parse.urljoin(base_url, f"articles/{article_id}/{slug}")
            else:
                article_url = urllib.parse.urljoin(base_url, f"articles/{article_id}")
            collected.append(article_url)

        last_page = int(data.get("last_page", page)) if isinstance(data, dict) else page
        if page >= last_page:
            break
        page += 1

    # Keep order stable while de-duplicating.
    seen: set[str] = set()
    deduped: list[str] = []
    for url in collected:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped[:max_pages]


def _w3g_urls(links: Iterable[str]) -> list[str]:
    return sorted({u for u in links if u.lower().endswith(".w3g")})


def _parse_iso8601(value: str) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _detect_latest_version_code(crawler: PoliteCrawler, base_url: str, filetype: str) -> str | None:
    api_url = urllib.parse.urljoin(base_url, "/api/v1/replays")
    payload: dict[str, object] = {"page": 1, "filetype": filetype}
    data = crawler.post_json(api_url, payload)
    if not isinstance(data, dict):
        return None
    rows = data.get("data", [])
    if not isinstance(rows, list) or not rows:
        return None
    latest = rows[0]
    if not isinstance(latest, dict):
        return None
    version_code = latest.get("version")
    return str(version_code) if version_code is not None else None


def _normalize_target_version(value: str) -> str:
    """Normalize user-friendly patch strings to API version codes.

    Examples:
    - "2.00" -> "00"
    - "1.36" -> "36"
    - "1.30.2" -> "30.2"
    - "36" -> "36"
    - "30.2" -> "30.2"
    """
    raw = value.strip()
    if not raw:
        return raw

    parts = raw.split(".")
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        major = int(parts[0])
        if major in (1, 2):
            # Treat Warcraft-style major.minor as API minor code.
            return parts[1].zfill(2)
        return raw

    if len(parts) == 3 and all(part.isdigit() for part in parts):
        major = int(parts[0])
        if major in (1, 2):
            # Treat Warcraft-style major.minor.patch as API minor.patch code.
            return f"{int(parts[1])}.{int(parts[2])}"
        return raw

    if re.fullmatch(r"\d+", raw) or re.fullmatch(r"\d+\.\d+", raw):
        return raw

    return raw


def _infer_major_version_from_input(value: str, default_major: int) -> int:
    raw = value.strip()
    if not raw:
        return default_major
    match = re.match(r"^(\d+)\.", raw)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return default_major
    return default_major


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


def _discover_replays_via_api(
    crawler: PoliteCrawler,
    base_url: str,
    *,
    filetype: str,
    min_elo: int,
    version: str | None,
    race_one: str | None,
    race_two: str | None,
    max_pages: int,
    max_replays: int,
    max_age_days: int,
) -> list[dict[str, object]]:
    api_url = urllib.parse.urljoin(base_url, "/api/v1/replays")
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    selected: list[dict[str, object]] = []

    for page in range(1, max_pages + 1):
        payload: dict[str, object] = {
            "page": page,
            "filetype": filetype,
            "minimumElo": min_elo,
        }
        if version:
            payload["version"] = version
        if race_one:
            payload["raceOne"] = race_one
        if race_two:
            payload["raceTwo"] = race_two

        try:
            data = crawler.post_json(api_url, payload)
        except Exception as exc:  # pragma: no cover - defensive for live web variability.
            print(f"[warn] failed API page {page}: {exc}")
            break

        if not isinstance(data, dict):
            break
        rows = data.get("data", [])
        if not isinstance(rows, list) or not rows:
            break

        page_has_fresh = False
        for replay in rows:
            if not isinstance(replay, dict):
                continue
            created_at = _parse_iso8601(str(replay.get("created_at", "")))
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at and created_at >= cutoff:
                page_has_fresh = True
            if created_at and created_at < cutoff:
                continue

            selected.append(replay)
            if len(selected) >= max_replays:
                return selected

        # Listing is newest-first; stop once an entire page is older than cutoff.
        if not page_has_fresh:
            break

    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="Polite Warcraft3.Info replay downloader")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--out-dir", default="replays/incoming")
    parser.add_argument(
        "--discovery-mode",
        choices=["api", "articles"],
        default="api",
        help="Use API filtering for relevant replays or article link discovery for direct .w3g links",
    )
    parser.add_argument("--max-pages", type=int, default=20, help="Max article pages to inspect")
    parser.add_argument("--max-replays", type=int, default=100, help="Max replay files to select")
    parser.add_argument("--max-age-days", type=int, default=30, help="Keep only replays newer than this many days")
    parser.add_argument("--min-elo", type=int, default=2200, help="Minimum replay Elo for API mode")
    parser.add_argument("--filetype", choices=["w3g", "nwg"], default="w3g")
    parser.add_argument(
        "--organize-by",
        choices=["flat", "matchup", "map", "matchup_map"],
        default="matchup_map",
        help="Folder layout for API downloads",
    )
    parser.add_argument(
        "--major-version",
        type=int,
        default=2,
        help="Warcraft major version used for full patch labels (default: 2)",
    )
    parser.add_argument(
        "--target-version",
        default="auto",
        help=(
            "Version filter (supports API codes like 00/26/36/30.2 and patch-like strings "
            "like 2.00, 1.36, 1.30.2) or 'auto' for newest"
        ),
    )
    parser.add_argument("--race-one", default=None, help="Optional race filter for first player side")
    parser.add_argument("--race-two", default=None, help="Optional race filter for second player side")
    parser.add_argument("--min-delay", type=float, default=4.0, help="Minimum seconds between requests")
    parser.add_argument("--max-jitter", type=float, default=2.0, help="Extra random delay range in seconds")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--backoff", type=float, default=2.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument(
        "--skip-ssl-verification",
        action="store_true",
        help="Disable certificate verification if the site presents an invalid TLS chain",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report links without downloading files")
    args = parser.parse_args()

    if args.max_pages <= 0:
        raise ValueError("--max-pages must be > 0")

    crawler = PoliteCrawler(
        base_url=args.base_url,
        user_agent=args.user_agent,
        min_delay_s=args.min_delay,
        max_jitter_s=args.max_jitter,
        timeout_s=args.timeout,
        retries=args.retries,
        backoff_s=args.backoff,
        insecure_skip_ssl_verification=args.skip_ssl_verification,
    )

    print(f"[info] robots: {urllib.parse.urljoin(args.base_url, 'robots.txt')}")
    print(
        "[info] crawl policy: "
        f"min-delay={args.min_delay:.1f}s jitter<= {args.max_jitter:.1f}s max-pages={args.max_pages}"
    )

    replay_urls: set[str] = set()
    api_replays: list[dict[str, object]] = []
    effective_major_version = args.major_version

    if args.discovery_mode == "articles":
        homepage = args.base_url
        homepage_html = crawler.fetch_html(homepage)
        homepage_links = _extract_links(homepage_html, args.base_url)
        article_urls = _article_urls(homepage_links, args.base_url)[: args.max_pages]
        if not article_urls:
            # Front page is JS-rendered; use public API listing as fallback discovery.
            article_urls = _article_urls_from_api(crawler, args.base_url, args.max_pages)

        print(f"[info] discovered {len(article_urls)} article pages to inspect")

        for index, article_url in enumerate(article_urls, start=1):
            try:
                article_html = crawler.fetch_html(article_url)
            except PermissionError as exc:
                print(f"[skip] {exc}")
                continue
            except Exception as exc:  # pragma: no cover - defensive for live web variability.
                print(f"[warn] failed to fetch {article_url}: {exc}")
                continue

            links = _extract_links(article_html, args.base_url)
            discovered = _w3g_urls(links)
            if discovered:
                print(f"[info] page {index}/{len(article_urls)} {article_url} -> {len(discovered)} replay links")
            for url in discovered:
                replay_urls.add(url)
    else:
        target_version = args.target_version
        major_version = args.major_version
        if target_version == "auto":
            auto_version = _detect_latest_version_code(crawler, args.base_url, args.filetype)
            target_version = auto_version or ""
            if target_version:
                print(f"[info] auto-detected latest version code: {target_version}")
                print(f"[info] effective patch label: {_format_patch_label(target_version, major_version)}")
            else:
                print("[warn] could not auto-detect latest version; continuing without version filter")
        else:
            major_version = _infer_major_version_from_input(target_version, major_version)
            normalized_version = _normalize_target_version(target_version)
            if normalized_version != target_version:
                print(f"[info] normalized target version '{target_version}' -> '{normalized_version}'")
                if re.fullmatch(r"[12]\.00", target_version):
                    print(
                        "[warn] patch strings 1.00 and 2.00 both normalize to API version code '00'; "
                        "prefer --target-version auto if you want the newest available code"
                    )
            target_version = normalized_version
            print(f"[info] effective patch label: {_format_patch_label(target_version, major_version)}")

        effective_major_version = major_version

        api_replays = _discover_replays_via_api(
            crawler,
            args.base_url,
            filetype=args.filetype,
            min_elo=args.min_elo,
            version=target_version or None,
            race_one=args.race_one,
            race_two=args.race_two,
            max_pages=args.max_pages,
            max_replays=args.max_replays,
            max_age_days=args.max_age_days,
        )
        print(f"[info] selected {len(api_replays)} API replays")

    if not replay_urls and not api_replays:
        print("[result] no relevant replays found")
        return 0

    out_dir = Path(args.out_dir)
    downloaded = 0
    if replay_urls:
        for replay_url in sorted(replay_urls):
            filename = Path(urllib.parse.urlparse(replay_url).path).name or "replay.w3g"
            target = out_dir / filename
            if args.dry_run:
                print(f"[dry-run] would download: {replay_url} -> {target}")
                continue
            if target.exists():
                print(f"[skip] exists: {target}")
                continue
            try:
                crawler.download_file(replay_url, target)
                downloaded += 1
                print(f"[ok] downloaded: {target}")
            except PermissionError as exc:
                print(f"[skip] {exc}")
            except Exception as exc:  # pragma: no cover - defensive for live web variability.
                print(f"[warn] failed download {replay_url}: {exc}")

    if api_replays:
        for replay in api_replays:
            replay_id = replay.get("id")
            if replay_id is None:
                continue
            patch_label = _format_patch_label(str(replay.get("version", "")), effective_major_version)
            target = _build_api_target_path(out_dir, replay, effective_major_version)
            if args.organize_by == "flat":
                target = out_dir / target.name
            elif args.organize_by == "matchup":
                target = out_dir / target.parent.parent.name / target.name
            elif args.organize_by == "map":
                target = out_dir / target.parent.name / target.name
            source_url = urllib.parse.urljoin(args.base_url, f"/api/v1/replays/{replay_id}/download")
            if args.dry_run:
                player_names: list[str] = []
                for p in replay.get("players", []):
                    if not isinstance(p, dict):
                        continue
                    stats_player = p.get("stats_player", {})
                    if isinstance(stats_player, dict) and stats_player.get("name"):
                        player_names.append(str(stats_player["name"]))
                    elif p.get("player"):
                        player_names.append(str(p["player"]))
                player_label = " vs ".join(player_names[:2]) if player_names else "unknown players"
                print(
                    "[dry-run] would download: "
                    f"id={replay_id} version={replay.get('version')} patch={patch_label} created={replay.get('created_at')} "
                    f"map={replay.get('map')} matchup={player_label} -> {target}"
                )
                continue
            if target.exists():
                print(f"[skip] exists: {target}")
                continue
            try:
                crawler.download_file(source_url, target)
                _write_replay_sidecar(target, replay, patch_label=patch_label, source_url=source_url)
                downloaded += 1
                print(f"[ok] downloaded: {target}")
            except PermissionError as exc:
                print(f"[skip] {exc}")
            except Exception as exc:  # pragma: no cover - defensive for live web variability.
                print(f"[warn] failed download replay id {replay_id}: {exc}")

    discovered_total = len(replay_urls) + len(api_replays)
    print(f"[result] replays selected: {discovered_total}; downloaded: {downloaded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
