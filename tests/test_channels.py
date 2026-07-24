from __future__ import annotations

import json
from pathlib import Path

from st4patcher.channels import (
    build_channel_map,
    channel_for,
    load_cache,
    parse_packages,
    write_cache,
)

PACKAGES_FIXTURE = """\
Package: sublime-text
Architecture: amd64
Version: 4205
Filename: files/sublime-text_build-4205_amd64.deb

Package: sublime-text
Architecture: arm64
Version: 4205
Filename: files/sublime-text_build-4205_arm64.deb

Package: sublime-merge
Architecture: amd64
Version: 2102
Filename: files/sublime-merge_build-2102_amd64.deb

Package: sublime-text
Architecture: amd64
Version: 4199
Filename: files/sublime-text_build-4199_amd64.deb
"""


def test_parse_packages_excludes_merge_and_dedups_arches() -> None:
    versions = parse_packages(PACKAGES_FIXTURE)

    assert versions == {"4205", "4199"}
    assert "2102" not in versions


def test_build_channel_map_stable_takes_precedence_over_dev() -> None:
    channel_map = build_channel_map(stable={"4106", "4200"}, dev={"4106", "4205"})

    assert channel_map["4200"] == "sublime-text-stable"
    assert channel_map["4205"] == "sublime-text-dev"
    assert channel_map["4106"] == "sublime-text-stable"


def test_channel_for_unknown_build_is_unlisted() -> None:
    channel_map = build_channel_map(stable={"4200"}, dev={"4205"})

    assert channel_for(9999, channel_map) == "unlisted-dev-builds"
    assert channel_for("4205", channel_map) == "sublime-text-dev"
    assert channel_for(4200, channel_map) == "sublime-text-stable"


def test_write_then_load_cache_round_trip(tmp_path: Path) -> None:
    cache = tmp_path / "official-versions.json"
    write_cache(cache, stable={"4200"}, dev={"4205", "4199"})

    raw = json.loads(cache.read_text())
    assert raw["stable"] == ["4200"]
    assert raw["dev"] == ["4205", "4199"]
    assert "_generated" in raw

    channel_map = load_cache(cache)
    assert channel_for(4205, channel_map) == "sublime-text-dev"
    assert channel_for(4200, channel_map) == "sublime-text-stable"


def test_load_cache_missing_file_is_empty(tmp_path: Path) -> None:
    assert load_cache(tmp_path / "absent.json") == {}


def test_committed_cache_has_expected_official_builds() -> None:
    cache_path = Path("downloads/official-versions.json")
    channel_map = load_cache(cache_path)

    assert channel_for(4205, channel_map) == "sublime-text-dev"
    assert channel_for(4200, channel_map) == "sublime-text-stable"
    assert channel_for(4199, channel_map) == "sublime-text-dev"
