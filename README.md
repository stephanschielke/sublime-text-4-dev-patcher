# sublime-text-4-dev-patcher

> [!IMPORTANT]
> **Intended use.** This project is a reverse-engineering
> record and patcher for **plugin-development testing** of the
> [Sublime Text 4](https://www.sublimetext.com/) (**Linux x64**) editor. 
> It is meant for developers testing their own plugins against
> `dev` builds (that all require a license), and for security/RE research on a copy the operator already
> owns. It ships **no Sublime binaries and no license keys**. If you use Sublime
> Text, [buy a license](https://www.sublimehq.com/store/text) and comply with
> its terms. See [`LICENSE`](LICENSE), [`DISCLAIMER.md`](DISCLAIMER.md), and
> [`NOTICE.md`](NOTICE.md).

*All I wanted to do was write an OSS plugin for [Sublime Text 4](https://www.sublimetext.com/) using the brand new [Python 3.14](https://docs.python.org/3/whatsnew/changelog.html#python-3-14-5-final) plugin host. But, as it turns out, the new plugin host is only enabled/available/testable with a [`dev` build](https://www.sublimetext.com/dev) of `4205` (or higher). No problem! Just switch release branches, download, install, and... wait... what is this? Did I break something?! Why can't I open my editor anymore?!*

For those unaware: any `dev` build **requires a license**. A developer who wants to test a plugin against the new host before it reaches a [stable release](https://www.sublimetext.com/download) either waits for the stable rollout, [buys a license](https://www.sublimehq.com/store/text) to test early, or studies how the startup license check works. This repository documents that reverse-engineering work and provides a repeatable patcher for a user-owned copy.

The patcher is **build-agnostic across builds `4176`-`4207`**: it resolves every
patch site structurally, not by hardcoded offsets. Below `4176` the binary
changes shape. Start with the [research index](research/README.md) for the full
reverse-engineering record.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/stephanschielke/sublime-text-4-dev-patcher)

## Layout

```
st4patcher/             the Python package (Python 3.12; capstone, pyelftools, debian-inspector)
  constants.py          patch SITES, recipe md5s, hosts block, signatures, VA_BIAS
  patcher.py            pure-logic primitives: md5 / report / apply_patches
  locate_sites.py       build-agnostic site locator: signatures + caller fingerprint (needs capstone)
  channels.py           derive official dev/stable build sets from the APT indices
  download.py           channel/filename/URL mapping (pure mirror of download.sh)
  __main__.py           `st4patch` CLI (--hosts/--no-update/--no-crash/--verify-only/--locate)
tests/                  pytest suite (pure-logic always runs; binary tests skip if absent)
binaries/               the binaries under test (git-ignored blobs)
  clean-original/4205-linux-amd64/sublime_text   pristine reference binary
  patches-candidates/   patched variants (PATCH-4205-A/-A-hosts/-B + EXP-* experiments)
downloads/              re-downloadable release artifacts (git-ignored blobs)
  download.sh           re-fetch any build/arch into the channel/build tree
  official-versions.json official dev/stable build sets (cached from the APT indices)
  EXPECTED_ARTIFACTS.md what a populated build dir looks like (indicator)
docs/                   project documentation
  TOOLS.md              tooling reference (llvm, pyelftools, objdump, capstone)
research/               Sublime reverse-engineering record + prior art
  README.md             RE documentation index (start here)
  sublime-4205-license-patch.md   primary RE record (glossary, sites, signatures, mermaid)
  cross-build-generalization.md   build-agnostic locator, 4176-4207 tables, 4175 roadblock
  sources-and-version-map.md      prior-art source links + version/OS/patch map
  RESEARCH_NOTES.md               prior-art overview (platform/version/strategy table)
  st4205-license-map.md / .json   raw string xrefs, relocs, disassembly dumps
  ELF/ objdumps/ string-dumps/    raw dumps (git-ignored)
  related-projects/               cloned reference repos (git-ignored)
```

## Toolchain

Python 3.12 via `mise` + `uv` (declares `capstone`, `pyelftools`, `debian-inspector`):

```bash
mise run setup    # create the .venv on Python 3.12
mise run sync     # resolve + install deps (incl. dev: ruff, pytest)
```

Common tasks: `mise run lint`, `mise run format`, `mise run test`,
`mise run locate`, `mise run verify`, `mise run check:scripts`,
`mise run channels:refresh`, `mise run download <build>`.

## Build channels

Each build is filed under one of three channels in the download tree:

| Channel               | Meaning                                                   |
|-----------------------|-----------------------------------------------------------|
| `sublime-text-stable` | listed in the official **stable** APT `Packages` index    |
| `sublime-text-dev`    | listed in the official **dev** APT `Packages` index       |
| `unlisted-dev-builds` | in neither index (released on the CDN but not advertised) |

The official dev/stable sets are parsed from Sublime's APT indices
(`download.sublimetext.com/apt/{dev,stable}/Packages`) with `debian-inspector`
and cached in `downloads/official-versions.json` (committed, so downloads work offline). A build present in both indices is treated as **stable**. Regenerate the cache from the live indices with:

```bash
mise run channels:refresh        # or: ./downloads/download.sh --refresh-channels <build>
```

## Quick start

```bash
# 0. (only for a brand-new build not yet in the committed cache) refresh the
#    channel list first, else download.sh cannot place it. The committed
#    official-versions.json lags the CDN, so a just-released build needs this
#    once:
mise run channels:refresh

# 1. fetch a build (re-downloadable; binaries are git-ignored)
./downloads/download.sh 4205        # or any build, e.g. 4206/4207

# 2. patch a user-owned copy of the clean binary (no sudo)
#    download.sh downloads the x64 tarball into downloads/<channel>/build-<N>/;
#    extract it manually and point --src at the extracted sublime_text
#    (or the committed 4205 reference).
uv run st4patch \
    --src binaries/clean-original/4205-linux-amd64/sublime_text \
    --out /tmp/sublime_text.patched
# expected out md5: 4eec4c3506773e9899cdbe8e463ab9c0  (recipe PATCH-4205-A)
# the patcher is build-agnostic: on 4206/4207 it auto-detects the valid-return
# convention (280) and self-verifies -- no per-build flags needed.

# 2b. fully hardened: license + phone-home block + updater + crash-report off
uv run st4patch --src <clean binary> --out /tmp/sublime_text.patched --hosts --no-update --no-crash

# 3. resolve patch offsets on any build (signatures + caller fingerprint)
uv run st4patch --src <clean binary> --locate
# -> prints the five offsets + inferred valid-return value; "LOCATE: MATCH" on clean 4205
# patching itself is build-agnostic: validated on 4176-4207 (31 builds, incl.
# 4201's magic-value convention). A descending battery hits a structural roadblock
# at 4175 (notify-function prologues recompiled); see research/ for the era boundary.
# (e.g. uv run st4patch --src 4204 --out /tmp/p --hosts)
```

## Network hardening (`--no-update`, `--no-crash`)

Both flags are opt-in, independent of the license patch, and redirect a phone-home host to `127.0.0.1` (NUL-padded, size-preserving) so the request never reaches Sublime's servers.

`--no-update` disables the "Update Available" popup that non-latest builds show on startup (dev builds chase the latest dev build, stable builds the latest stable). It redirects **both**:

- the updater's dedicated host copy `www.sublimetext.com` -> `127.0.0.1`, so the update check never leaves the machine (this is the copy flanked by the
  `latest_version` label, NOT the shared `https://www.sublimetext.com/buy` copy, which is left intact); and
- its channel-specific path `/updates/4/{dev,stable}_update_check?version=...`
  (the unique build-agnostic anchor) -> `/dev/null...`, a 404 route, as defense-in-depth.

`--no-crash` redirects the bundled `crash_handler`'s upload host
`crash-server.sublimehq.com` -> `127.0.0.1`, so minidumps are never uploaded on a crash. (Equivalently, `chmod a-x crash_handler` also works -- Sublime starts fine without an executable handler -- but the string redirect travels with the binary.)

Sublime also honors `"update_check": false` in
`Packages/User/Preferences.sublime-settings`; `--no-update` is the binary-level,
settings-independent equivalent for a build whose startup checks have been
patched.

See `research/README.md` for the RE documentation index, and
`research/sublime-4205-license-patch.md` for the full record, the EXP-VTABLE / EXP-RET0 / EXP-RET1 experiment vocabulary, and the PATCH-4205-A/-A-hosts/-B recipes. Source attributions and the cross-version SublimeText+OS+patch map are in `research/sources-and-version-map.md`.
