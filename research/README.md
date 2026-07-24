# Research and reverse-engineering index

> **Reverse-engineering documentation — educational / research use only.** Every
> document in this directory records interoperability and security research on
> operator-owned copies of Sublime Text. It ships no Sublime binaries or license
> keys. Sublime Text is proprietary software of Sublime HQ Pty Ltd; this project
> is **not affiliated with or endorsed by Sublime HQ**. If you use Sublime Text,
> [buy a license](https://www.sublimehq.com/store/text). See the repository
> [`LICENSE`](../LICENSE), [`DISCLAIMER.md`](../DISCLAIMER.md), and
> [`NOTICE.md`](../NOTICE.md).

Reverse-engineering record for the Sublime Text 4 (Linux x64) startup license window, and the build-agnostic patcher derived from it. The patcher is validated across **builds 4176-4206**; below 4176 the binary changes shape (see the roadblock note in the cross-build record).

Read in this order.

## 1. Primary record (start here)

- [`sublime-4205-license-patch.md`](sublime-4205-license-patch.md) - the central document. Glossary, the five patch sites, byte signatures, before/after control-flow diagrams, the PATCH-4205-A/-A-hosts/-B recipes, the repeatable procedure, and the signature method for finding the sites in a future build. Worked through on build 4205; the locator generalizes it to 4176-4206.

## 2. Cross-build generalization

- [`cross-build-generalization.md`](cross-build-generalization.md) - how the patcher became build-agnostic across 4176-4206: the caller-fingerprint locator, the (non-monotonic) IsValidLicense return convention, per-build offset and md5 tables, the network-hardening flags, and the **4175 roadblock** (notify-function prologues recompiled). **This is the authority for per-build facts.**

## 3. Prior art and version map

- [`sources-and-version-map.md`](sources-and-version-map.md) - prior-art source URLs (cited by their real GitHub / gist links) and the consolidated SublimeText x OS x patch mapping table.
- [`RESEARCH_NOTES.md`](RESEARCH_NOTES.md) - high-level prior-art overview (platform/version/strategy table). Raw recipes at the cited URLs.

## 4. Raw data dumps (reference)

- [`st4205-license-map.md`](st4205-license-map.md) /
  [`.json`](st4205-license-map.json) - raw string xrefs, accessor relocations, and `readelf`/`objdump` disassembly dumps for build 4205.

## Related

- Tooling reference (llvm, pyelftools, objdump, capstone):
  [`../docs/TOOLS.md`](../docs/TOOLS.md).
- The patcher itself lives in the [`st4patcher/`](../st4patcher) package; run it with `uv run st4patch --help`.

## Naming conventions (keep consistent across all docs)

- **Experiments:** `EXP-VTABLE` (failed, vtable-dispatched), `EXP-RET0` (failed on 4205, IsValidLicense -> 0), `EXP-RET1` (works on 4205, -> 1).
- **Recipes:** `PATCH-4205-A` (full 5-site, working), `PATCH-4205-A-hosts`,
  `PATCH-4205-B` (IsValidLicense-only).
- **The IsValidLicense return convention is NOT a clean `< 4205` / `>= 4205`
  boundary.** The value a build treats as valid is non-monotonic: `0` on 4176-4200/4203/4204, `1` on 4202/4205, `0x118` on 4201, `280` on 4206. The locator reads it per build from the caller's `cmp`; see
  [`cross-build-generalization.md`](cross-build-generalization.md).
- Cite real GitHub URLs only; no informal author names in prose.
