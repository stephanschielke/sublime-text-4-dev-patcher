"""Pure-Python mirror of ``download.sh`` mapping logic.

Provides build-to-channel mapping, artifact filename templates, and URL/path
composition - all unit-testable without network.

Channel assignment is delegated to :mod:`st4patcher.channels`, which derives the
official dev/stable build sets from Sublime's APT ``Packages`` indices (cached in
``downloads/official-versions.json``). Builds in neither set are unlisted.
"""

from __future__ import annotations

from pathlib import Path

from st4patcher.channels import UNLISTED_CHANNEL, load_cache
from st4patcher.channels import channel_for as _channel_for

CDN = "https://download.sublimetext.com"

DEFAULT_CHANNEL = UNLISTED_CHANNEL

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / "downloads" / "official-versions.json"

# Artifact key -> filename template.  ``{N}`` is replaced by the build number.
ARTIFACT_TEMPLATES: dict[str, str] = {
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

ALL_ARCH_KEYS: tuple[str, ...] = tuple(ARTIFACT_TEMPLATES.keys())


# ---------------------------------------------------------------------------
#  Build -> channel
# ---------------------------------------------------------------------------


def channel_for(build: int, cache_path: Path = DEFAULT_CACHE_PATH) -> str:
    """Return the channel directory name for a given build number.

    Reads the official-versions cache (``downloads/official-versions.json``):
    stable builds -> ``sublime-text-stable``, dev builds -> ``sublime-text-dev``,
    everything else (or no cache) -> ``unlisted-dev-builds``.
    """
    return _channel_for(build, load_cache(cache_path))


# ---------------------------------------------------------------------------
#  Filename / URL / path helpers
# ---------------------------------------------------------------------------


def filename_for(arch_key: str, build: int) -> str:
    """Return the remote filename for *arch_key* at *build*.

    Raises ``KeyError`` if *arch_key* is not a recognised artifact key.
    """
    template = ARTIFACT_TEMPLATES[arch_key]  # let KeyError propagate
    return template.replace("{N}", str(build))


def url_for(arch_key: str, build: int) -> str:
    """Full download URL for *arch_key* at *build* (``CDN/filename``)."""
    return f"{CDN}/{filename_for(arch_key, build)}"


def relpath_for(arch_key: str, build: int) -> Path:
    """Relative output path: ``<channel>/build-<build>/<filename>``."""
    path = Path(channel_for(build)) / f"build-{build}" / filename_for(arch_key, build)
    return path
