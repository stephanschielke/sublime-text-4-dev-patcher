# Sources and version map

> **Reverse-engineering documentation — educational / research use only.**
> Prior-art references and a version/patch mapping table, including byte facts
> from operator-owned copies. Sublime Text is proprietary software of Sublime HQ
> Pty Ltd; this project is **not affiliated with or endorsed by Sublime HQ** and
> ships no Sublime binaries or license keys. If you use Sublime Text,
> [buy a license](https://www.sublimehq.com/store/text). See the repository
> `LICENSE`, `DISCLAIMER.md`, and `NOTICE.md`.

All prior-art patch recipes referenced by this project, cited by their **real
GitHub repository / gist URL** (the URL owner is the canonical attribution; no
informal nicknames are used in prose). Followed by a consolidated
**SublimeText version + OS + patch** mapping table.

Raw extracts of every snippet live in
`research/RESEARCH_NOTES.md` (condensed overview; raw recipes at the cited URLs).

## 1. Canonical sources (real links)

| ID | Source URL | Scope (version + OS) | Strategy |
|---|---|---|---|
| SRC-PATCHER | https://github.com/rainbowpigeon/sublime-text-4-patcher | ST4 4107-4206, Windows x64 | signature scan + `ret0`/`ret1` enum patch; the reference architecture |
| SRC-PATCHER-FORK | https://github.com/rainbowpigeon/sublime-text-4-patcher/compare/main...ToastyTheBot:sublime-text-4-patcher:license_check_direct_prologue | ST4, Windows x64 | adds direct `license_check` prologue signatures |
| SRC-RUST-4200 | https://github.com/ZEERDEER/SublimeText4License (tag `4200+`, file `SublimeText4License_ver.4200+.rs`) | ST4 4200, Windows x64 | byte find/replace: `74 06 3B`→`EB 06 3B`, `89 F8 …`→`33 C0 …` |
| SRC-RUST-4000 | https://github.com/ZEERDEER/SublimeText4License (tag `4200+`, file `SublimeText4License.rs`) | ST4 4000-4199, Windows x64 | `80 79 05 00 0F 94 C2`→`C6 41 05 01 B2 00 90` |
| SRC-GIST-FADI | https://gist.github.com/Fadi002/51a505cece648915bc2f32f3b7e6b71d | ST4 4200, Windows x64 + Linux | offset NOP table; `0F B6 51 05 83 F2 01`→`C6 41 05 01 B2 00 90` |
| SRC-GIST-JERRY | https://gist.github.com/JerryLokjianming/71dac05f27f8c96ad1c8941b88030451 | ST4 4107 Windows; Sublime Merge 2121 Linux | RSA-fn + host-string replace |
| SRC-REPO-QZ | https://github.com/qzzhoulu1995/sublime | ST4 4200, macOS x86_64 + Windows | `movzx edx,[rcx+5]; xor edx,1` → force-registered |
| SRC-GIST-WAL | https://gist.github.com/walbarellos/e60a1f8b713cc961a3156da525b889f1 | ST3 3211, ST4 alpha 4094/4098, Linux + macOS + Windows | hex-editor offset edits / perl substitution |
| SRC-GIST-OPA | https://gist.github.com/opastorello/05f02f902339ebc27ea7f20c1838b066 | ST4 4121 | tutorial / concepts |
| SRC-GIST-DEST | https://gist.github.com/Destitute-Streetdwelling-Guttersnipe/29b4fe8470930148ea91050fd6a1b703 | ST4 4126, macOS | `80 78 05 00 0F 94 C1`→`C6 40 05 01 48 85 C9` |
| SRC-GIST-LINUX-4200 | https://gist.github.com/maboloshi/feaa63c35f4c2baab24c9aaf9b3f4e47 (comment 5597063) | ST4 4200, Linux x64 | **5-site `xxd` recipe this project ports to 4205** |
| SRC-GIST-MAC-4200 | https://gist.github.com/maboloshi/feaa63c35f4c2baab24c9aaf9b3f4e47 (comment 5926642) | ST4 4200, macOS ARM64 + x86_64 | 5-site recipe, AArch64 + Intel variants |
| SRC-ISSUE-23 | https://github.com/rainbowpigeon/sublime-text-4-patcher/issues/23#issuecomment-3881489429 | ST4 4200, Linux x64 + macOS x86_64 | `IsValidLicense → B0 00 C3` + flag-store patches |

> The 5-site Linux recipe this project builds on is **SRC-GIST-LINUX-4200**. We
> port it forward to Build 4205 (see version map row 4205/Linux).

## 2. Strategy vocabulary

Experiments are named by the **strategy** they test:

| Strategy ID | What it patches | Return convention | Outcome |
|---|---|---|---|
| **EXP-VTABLE** | the vtable getter `0x6194c8` and/or the dialog builder `0x550ee3` | n/a | FAILED - getters are vtable-dispatched, so overwriting the getter body never changed the dispatched call result; the window persisted |
| **EXP-RET0** | the real `IsValidLicense` enum function + 4 neighbours, `IsValidLicense → return 0` | returns **0** | FAILED on 4205 - every caller does `cmp eax,1`, so 0 reads as invalid |
| **EXP-RET1** | the same 5 sites, but `IsValidLicense → return 1` | returns **1** | WORKS - matches the 4205 valid-enum boundary |

`EXP-RET0` is the straight forward-port of **SRC-GIST-LINUX-4200** (which used
`mov rax,0` because pre-4205 callers compared against 0). `EXP-RET1` is the
one-instruction fix required by the 4205 `cmp eax,1` convention.

## 3. Patch recipes (deliverables)

The shippable recipes encoded in `st4patcher/constants.py`:

| Recipe ID | Sites | IsValidLicense | Adds hosts block | md5 (4205) | Status |
|---|---|---|---|---|---|
| **PATCH-4205-A** | all 5 | `xor rax,rax; inc rax; ret` (=1) | no | `4eec4c3506773e9899cdbe8e463ab9c0` | **CONFIRMED WORKING** |
| **PATCH-4205-A-hosts** | all 5 + hosts | =1 | yes (`license.sublimehq.com`→`127.0.0.1`) | `b2ad2138435a548bbe7093a5807bba30` | works (defense-in-depth) |
| **PATCH-4205-B** | IsValidLicense only | =1 | no | `d36770200e4c710854b969dc77baff3e` | minimal (single-site) |

Clean reference binary md5: `c7539dda818f0c3537ba6cfa0f872fa9`.

## 4. SublimeText version + OS + patch mapping

| SublimeText | OS / arch | Key bytes (original → patched) | Source | Strategy class |
|---|---|---|---|---|
| ST3 3211 | Windows / Linux x64 | offset edits `0x8545 84→85`, `0x8FF19 75→EB`, `0x1932C7 75→74` | SRC-GIST-WAL | offset edit |
| ST4 a4094 | Linux / macOS / Windows | `97 94 0D`→`00 00 00`; or `0F B6 51 05 83 F2 01`→`C6 41 05 01 B2 00 90` | SRC-GIST-WAL | flag-store force |
| ST4 a4098 | Windows x64 | addr `0xA700` `80 38 00`→`FE 00 90` | SRC-GIST-WAL | flag-store force |
| ST4 4000-4199 | Windows x64 | `80 79 05 00 0F 94 C2`→`C6 41 05 01 B2 00 90` | SRC-RUST-4000 | flag-store force |
| ST4 4107 | Windows x64 | RSA-fn `41 57 41 56 56 57 55 53 …`→`33 C0 FE C0 C3 …`; host string→`sublimehq.localhost` | SRC-GIST-JERRY | RSA-fn + host |
| ST4 4121 | (tutorial) | concepts only | SRC-GIST-OPA | n/a |
| ST4 4126 | macOS | `80 78 05 00 0F 94 C1`→`C6 40 05 01 48 85 C9` | SRC-GIST-DEST | flag-store force |
| ST4 4200 | Windows x64 | `74 06 3B`→`EB 06 3B`; `89 F8 …`→`33 C0 …`; or `0F B6 51 05 83 F2 01`→`C6 41 05 01 B2 00 90` (Win off `0x46B80`) | SRC-RUST-4200, SRC-GIST-FADI | flag-store force |
| ST4 4200 | macOS x86_64 | `0F B6 51 05 83 F2 01`→`C6 41 05 01 B2 00 90` (off `0x290500`); or 5-site `xxd` recipe | SRC-REPO-QZ, SRC-GIST-MAC-4200 | EXP-RET1 (5-site) |
| ST4 4200 | macOS ARM64 | `00239DCF: 48 C7 C0 00 00 00 00 C3` + 4 AArch64 NOP/RET sites | SRC-GIST-MAC-4200 | EXP-RET0 (5-site) |
| ST4 4200 | Linux x64 | 5-site `xxd` recipe; md5 `cf2ba60236f6284da1581e29c3df35e7`→`fafcd973c631fcea17d77b04bbbb9652`; or perl `0F B6 51 05 83 F2 01`→`C6 41 05 01 B2 00 90` | SRC-GIST-LINUX-4200, SRC-ISSUE-23, SRC-GIST-FADI | EXP-RET0 (5-site) |
| **ST4 4205** | **Linux x64** | **5-site recipe ported forward; `IsValidLicense → xor rax,rax; inc rax; ret` (=1)** | **this project (ports SRC-GIST-LINUX-4200)** | **EXP-RET1 → PATCH-4205-A** |
| **ST4 4206** | **Linux x64** | **5-site recipe; `IsValidLicense → mov eax,280; ret`** | **this project (same locator)** | **280 → PATCH-4206-A** |
| ST4 4107-4206 | Windows x64 | signature-scanned `ret0`(<4205)/`ret1`(>=4205) enum patch | SRC-PATCHER | EXP-RET0/RET1 (signature) |
| Sublime Merge 2112/2121 | Linux x64 | `48 C7 C0 01 00 00 00 C3` at fn start (NOT Sublime Text) | SRC-GIST-MAC-4200, SRC-GIST-JERRY | n/a |

### The IsValidLicense return convention (not a clean 4205 boundary)

Forward-porting the Linux 4200 recipe to 4205 without flipping the return value
is exactly why the first 4205 attempt failed (4205 callers do `cmp eax,1`, so a
returned 0 reads as invalid); flipping it to 1 produced the working
**PATCH-4205-A**. That made it look like a tidy "`< 4205` returns 0 / `>= 4205`
returns 1" boundary.

**A later cross-build sweep disproved the tidy boundary.** The value a build
treats as "valid" is **not monotonic** in the build number:

| valid return | builds |
|--------------|--------|
| `0` (callers `test eax,eax`) | 4176-4200, 4203, 4204 |
| `1` (callers `cmp eax,1`) | 4202, 4205 |
| `0x118` (callers `cmp eax,0x118`) | 4201 only (a status code, not a bool) |
| 280 | 4206 (callers `cmp eax,280`) |

So the patcher never assumes a value: it reads the immediate from each caller's
compare and emits the matching return stub. Full per-build evidence:
[`cross-build-generalization.md`](cross-build-generalization.md).
