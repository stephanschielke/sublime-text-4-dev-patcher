#!/usr/bin/env bash
#
# Download Sublime Text release artifacts into this repo's directory layout.
#
# All artifacts are served from a single flat CDN host:
#     https://download.sublimetext.com/<artifact-filename>
# This script reconstructs them into the per-channel / per-build tree:
#     <channel>/build-<N>/<artifact-filename>
# where <channel> is "sublime-text-stable", "sublime-text-dev", or
# "unlisted-dev-builds".
#
# A build's channel is decided by the official APT `Packages` indices, cached in
# official-versions.json next to this script: stable builds -> sublime-text-stable,
# dev builds -> sublime-text-dev, anything in neither list -> unlisted-dev-builds.
# Regenerate that cache with `--refresh-channels` (or `mise run channels:refresh`).
#
# Usage:
#   ./download.sh <build> [<build> ...]         # e.g. ./download.sh 4205
#   ./download.sh --refresh-channels <build>    # refresh the cache first, then fetch
#   ARCHES="x64_linux mac" ./download.sh 4205   # subset of artifacts
#
# Env:
#   ARCHES   space-separated artifact keys to fetch (default: all)
#            keys: win  mac  x64_linux  x64_tar  arm_tar  amd_deb  arm_deb
#                  rpm  pkg_x86  pkg_arm
#   DEST     output root (default: directory of this script)
#   FORCE    "1" to re-download even if the file already exists

set -euo pipefail

CDN="https://download.sublimetext.com"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${DEST:-$HERE}"
CACHE="$HERE/official-versions.json"

# Resolve a build's channel from the official-versions cache using stdlib python
# (no jq dependency). Falls back to unlisted-dev-builds when the cache or key is
# absent, matching st4patcher.channels.channel_for.
channel_for() {
  local build="$1"
  python3 - "$CACHE" "$build" <<'PY'
import json, sys
cache, build = sys.argv[1], sys.argv[2]
try:
    data = json.load(open(cache))
except OSError:
    print("unlisted-dev-builds"); sys.exit(0)
if build in data.get("stable", []):
    print("sublime-text-stable")
elif build in data.get("dev", []):
    print("sublime-text-dev")
else:
    print("unlisted-dev-builds")
PY
}

refresh_channels() {
  echo ">> refreshing official-versions cache from the APT indices"
  uv run python -m st4patcher.channels --write "$CACHE"
}

# Artifact key -> filename template. {N} is replaced by the build number.
# Filename conventions are Sublime's own and differ by package type.
declare -A ARTIFACTS=(
  [win]="sublime_text_build_{N}_x64_setup.exe"
  [mac]="sublime_text_build_{N}_mac.zip"
  [x64_linux]="sublime_text_build_{N}_x64.zip"
  [x64_tar]="sublime_text_build_{N}_x64.tar.xz"
  [arm_tar]="sublime_text_build_{N}_arm64.tar.xz"
  [amd_deb]="sublime-text_build-{N}_amd64.deb"
  [arm_deb]="sublime-text_build-{N}_arm64.deb"
  [rpm]="sublime-text-{N}-1.x86_64.rpm"
  [pkg_x86]="sublime-text-{N}-1-x86_64.pkg.tar.xz"
  [pkg_arm]="sublime-text-{N}-1-aarch64.pkg.tar.xz"
)
ALL_KEYS="win mac x64_linux x64_tar arm_tar amd_deb arm_deb rpm pkg_x86 pkg_arm"

fetch_build() {
  local build="$1"
  local channel out_dir keys key file url out
  channel="$(channel_for "$build")"
  out_dir="$DEST/$channel/build-$build"
  mkdir -p "$out_dir"
  keys="${ARCHES:-$ALL_KEYS}"

  echo ">> build $build -> $channel/build-$build"
  for key in $keys; do
    file="${ARTIFACTS[$key]/\{N\}/$build}"
    if [[ -z "$file" ]]; then
      echo "   ?? unknown arch key: $key" >&2
      continue
    fi
    url="$CDN/$file"
    out="$out_dir/$file"
    if [[ -f "$out" && "${FORCE:-0}" != "1" ]]; then
      echo "   == exists: $file"
      continue
    fi
    echo "   -> $file"
    curl -fSL --retry 3 --retry-delay 2 -o "$out.part" "$url" \
      && mv "$out.part" "$out" \
      || { echo "   !! failed: $url" >&2; rm -f "$out.part"; }
  done
}

main() {
  local builds=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --refresh-channels)
        refresh_channels
        shift
        ;;
      -*)
        echo "unknown option: $1" >&2
        exit 1
        ;;
      *)
        builds+=("$1")
        shift
        ;;
    esac
  done

  if [[ ${#builds[@]} -eq 0 ]]; then
    grep -E '^# ' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' | head -24
    exit 1
  fi

  for b in "${builds[@]}"; do
    fetch_build "$b"
  done
  echo "done."
}

main "$@"
