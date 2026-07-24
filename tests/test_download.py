from __future__ import annotations

import json
from pathlib import Path

import pytest

from st4patcher.download import (
    ALL_ARCH_KEYS,
    ARTIFACT_TEMPLATES,
    CDN,
    DEFAULT_CHANNEL,
    channel_for,
    filename_for,
    relpath_for,
    url_for,
)


def test_public_constants_match_download_sh() -> None:
    assert CDN == "https://download.sublimetext.com"
    assert DEFAULT_CHANNEL == "unlisted-dev-builds"
    assert ARTIFACT_TEMPLATES == {
        "win": "sublime_text_build_{N}_x64_setup.exe",
        "mac": "sublime_text_build_{N}_mac.zip",
        "x64_linux": "sublime_text_build_{N}_x64.zip",
        "x64_tar": "sublime_text_build_{N}_x64.tar.xz",
        "arm_tar": "sublime_text_build_{N}_arm64.tar.xz",
        "amd_deb": "sublime-text_build-{N}_amd64.deb",
        "arm_deb": "sublime-text_build-{N}_arm64.deb",
        "rpm": "sublime-text-{N}-1.x86_64.rpm",
        "pkg_x86": "sublime-text-{N}-1-x86_64.pkg.tar.xz",
        "pkg_arm": "sublime-text-{N}-1-aarch64.pkg.tar.xz",
    }
    assert ALL_ARCH_KEYS == (
        "win",
        "mac",
        "x64_linux",
        "x64_tar",
        "arm_tar",
        "amd_deb",
        "arm_deb",
        "rpm",
        "pkg_x86",
        "pkg_arm",
    )


def test_channel_for_uses_cache(tmp_path: Path) -> None:
    cache = tmp_path / "official-versions.json"
    cache.write_text(json.dumps({"stable": ["4200"], "dev": ["4199", "4205"]}))

    assert channel_for(4199, cache) == "sublime-text-dev"
    assert channel_for(4200, cache) == "sublime-text-stable"
    assert channel_for(4205, cache) == "sublime-text-dev"
    assert channel_for(4202, cache) == "unlisted-dev-builds"


def test_channel_for_missing_cache_is_unlisted(tmp_path: Path) -> None:
    assert channel_for(4205, tmp_path / "absent.json") == "unlisted-dev-builds"


def test_filename_for_matches_templates() -> None:
    build = 4205
    assert filename_for("win", build) == "sublime_text_build_4205_x64_setup.exe"
    assert filename_for("mac", build) == "sublime_text_build_4205_mac.zip"
    assert filename_for("x64_linux", build) == "sublime_text_build_4205_x64.zip"
    assert filename_for("x64_tar", build) == "sublime_text_build_4205_x64.tar.xz"
    assert filename_for("arm_tar", build) == "sublime_text_build_4205_arm64.tar.xz"
    assert filename_for("amd_deb", build) == "sublime-text_build-4205_amd64.deb"
    assert filename_for("arm_deb", build) == "sublime-text_build-4205_arm64.deb"
    assert filename_for("rpm", build) == "sublime-text-4205-1.x86_64.rpm"
    assert filename_for("pkg_x86", build) == "sublime-text-4205-1-x86_64.pkg.tar.xz"
    assert filename_for("pkg_arm", build) == "sublime-text-4205-1-aarch64.pkg.tar.xz"


def test_filename_for_bad_arch_raises_key_error() -> None:
    with pytest.raises(KeyError):
        filename_for("nope", 4205)


def test_url_for_composes_with_cdn() -> None:
    assert url_for("x64_linux", 4205) == "https://download.sublimetext.com/sublime_text_build_4205_x64.zip"


def test_relpath_for_composes_channel_build_and_filename() -> None:
    assert relpath_for("x64_linux", 4205) == Path("sublime-text-dev/build-4205/sublime_text_build_4205_x64.zip")
    assert relpath_for("mac", 4202) == Path("unlisted-dev-builds/build-4202/sublime_text_build_4202_mac.zip")
