"""Derive official Sublime Text build channels from the APT ``Packages`` indices.

Sublime publishes two APT repositories whose ``Packages`` index lists every
officially released build as a ``sublime-text`` package paragraph:

    dev     https://download.sublimetext.com/apt/dev/Packages
    stable  https://download.sublimetext.com/apt/stable/Packages

A build that appears in neither index is an *unlisted* dev build (released on
the flat CDN but not advertised through APT). The mapping is cached to a small
committed JSON file so downloads work offline and the official set is reviewable
in git; ``--write`` regenerates it from the live indices.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from debian_inspector.debcon import get_paragraphs_data

PACKAGES_URLS: dict[str, str] = {
    "dev": "https://download.sublimetext.com/apt/dev/Packages",
    "stable": "https://download.sublimetext.com/apt/stable/Packages",
}

STABLE_CHANNEL = "sublime-text-stable"
DEV_CHANNEL = "sublime-text-dev"
UNLISTED_CHANNEL = "unlisted-dev-builds"


def parse_packages(text: str) -> set[str]:
    """Return the set of ``sublime-text`` build versions in a ``Packages`` index.

    The index also contains ``sublime-merge`` paragraphs and one paragraph per
    architecture; both are collapsed here to a set of distinct build numbers.
    """
    return {
        para["version"]
        for para in get_paragraphs_data(text)
        if para.get("package") == "sublime-text" and para.get("version")
    }


def _fetch_text(url: str, *, timeout: float = 30.0, retries: int = 3) -> str:
    last: Exception | None = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except urllib.error.URLError as exc:
            last = exc
    raise RuntimeError(f"could not fetch {url}: {last}")


def fetch_official_versions() -> dict[str, set[str]]:
    """Download and parse both APT indices. Touches the network."""
    return {channel: parse_packages(_fetch_text(url)) for channel, url in PACKAGES_URLS.items()}


def versions_from_paths(paths: dict[str, Path]) -> dict[str, set[str]]:
    """Parse already-downloaded ``Packages`` files (offline path).

    *paths* maps a channel name (``stable``/``dev``) to a local index file.
    """
    return {channel: parse_packages(path.read_text()) for channel, path in paths.items()}


def build_channel_map(stable: set[str], dev: set[str]) -> dict[str, str]:
    """Map each official build to its channel, stable taking precedence over dev."""
    channel_map = dict.fromkeys(dev, DEV_CHANNEL)
    channel_map.update(dict.fromkeys(stable, STABLE_CHANNEL))
    return channel_map


def channel_for(build: int | str, channel_map: dict[str, str]) -> str:
    """Channel directory for *build*, or ``unlisted-dev-builds`` when unknown."""
    return channel_map.get(str(build), UNLISTED_CHANNEL)


def write_cache(path: Path, stable: set[str], dev: set[str]) -> None:
    """Write the official-versions cache JSON (sorted numerically, newest first)."""
    payload = {
        "_generated": datetime.now(UTC).isoformat(),
        "_sources": PACKAGES_URLS,
        "stable": sorted(stable, key=int, reverse=True),
        "dev": sorted(dev, key=int, reverse=True),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_cache(path: Path) -> dict[str, str]:
    """Load a cache JSON and return its ``build -> channel`` map.

    Returns an empty map when the file is missing, so callers degrade to
    ``unlisted-dev-builds`` rather than failing offline.
    """
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return build_channel_map(set(raw.get("stable", [])), set(raw.get("dev", [])))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="derive official Sublime Text build channels")
    parser.add_argument(
        "--write",
        type=Path,
        metavar="PATH",
        help="write the cache JSON to PATH",
    )
    parser.add_argument(
        "--stable-file",
        type=Path,
        help="parse this local stable Packages index instead of fetching",
    )
    parser.add_argument(
        "--dev-file",
        type=Path,
        help="parse this local dev Packages index instead of fetching",
    )
    args = parser.parse_args(argv)

    if args.stable_file and args.dev_file:
        versions = versions_from_paths({"stable": args.stable_file, "dev": args.dev_file})
    else:
        versions = fetch_official_versions()
    stable, dev = versions["stable"], versions["dev"]

    if args.write:
        write_cache(args.write, stable, dev)
        print(f"wrote {args.write}: {len(stable)} stable, {len(dev)} dev versions")
    else:
        print(f"stable: {len(stable)} versions\ndev: {len(dev)} versions")
        print(f"newest stable: {max(stable, key=int)}  newest dev: {max(dev, key=int)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
