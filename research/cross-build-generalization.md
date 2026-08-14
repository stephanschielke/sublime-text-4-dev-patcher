# Cross-build generalization (4176-4207, build-agnostic patcher)

The original patcher hardcoded 4205 file offsets and keyed IsValidLicense on the
exact byte signature `83 F8 01 0F 94 47 05` (`cmp eax,1; sete [rdi+5]`). That
signature is 4205-specific, so the patcher could not patch 4204. This document
records the RE that made the patcher build-agnostic.

## What actually changes between builds

Reverse-engineering 4204 vs 4205 found only **two** structural differences at the
license gate; everything else (the two revalidation NOP calls, the two notify
prologues, the phone-home string) is byte-identical or trivially relocatable.

1. **IsValidLicense return convention varies.** The callers reveal what value
   they treat as "valid":
   - `test eax,eax; ... sete [reg+disp]` => valid == **0** (4176-4200 except 4201, plus 4203, 4204).
   - `cmp eax,1; ... sete [reg+disp]` => valid == **1** (4202, 4205).
   - `cmp eax,0x118; ... sete [reg+disp]` => valid == **0x118** (4201 only -- a
     status code, not a bool).
2. **Registered-flag store offset moved.**
   - 4204 stores the bool to `[rdi+0xc]`; 4205 to `[rdi+5]`.

The convention does NOT follow a clean "< 4205 returns 0 / >= 4205 returns 1"
boundary: 4202 already returns 1, and 4201 returns the magic value 0x118. The
locator therefore never assumes a value -- it reads the immediate from each
caller's compare and emits the matching return stub (see below).

## The build-agnostic locator

`st4patcher/locate_sites.py` resolves all five sites by structure:

- **nop1 / nop2**: anchored on `mov edx,0x1388` (`ba 88 13 00 00`) + the two
  following calls to the same target. Unique in both builds.
- **ret_notify1 / ret_notify2**: unique prologue signatures, present in both.
- **IsValidLicense**: found by **caller fingerprint**, not a byte signature:
  1. Bound the license cluster by the two notify prologues; scan E8 rel32 calls
     whose target lands in `[min(ret), max(ret)+0x100)`.
  2. Keep the target with >=2 callers where, within ~0x16 bytes of the call,
     capstone sees `sete [reg+disp8]` preceded by `cmp eax,1` or `test eax,eax`.
  3. Exactly one function survives in each build.
  4. The caller compare reveals the convention: `cmp eax,<imm>` => valid==imm
     (1 on 4202/4205, 0x118 on 4201), `test eax,eax` => valid==0. The winning
     value is the majority vote across callers. This drives the patch payload,
     so the patcher never hardcodes the return value.

Ambiguity (zero or several candidates) is reported as a hard error, never
guessed - a build whose gate is dispatched purely through a vtable will fail
loudly rather than be mis-patched.

## Per-build offset table (fileoff; .text VA = fileoff + 0x1000)

| site            | 4199      | 4200      | 4201      | 4202      | 4203      | 4204      | 4205      | 4206      | 4207      |
|-----------------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|
| nop1            | 0x556721  | 0x571483  | 0x55b59b  | 0x55b5cb  | 0x53b067  | 0x53b067  | 0x53b097  | 0x537057  | 0x538007  |
| nop2            | 0x55673a  | 0x57149c  | 0x55b5b4  | 0x55b5e4  | 0x53b080  | 0x53b080  | 0x53b0b0  | 0x537070  | 0x538020  |
| ret_notify1     | 0x569578  | 0x584378  | 0x56d774  | 0x56d788  | 0x54d258  | 0x54d260  | 0x54d288  | 0x549254  | 0x54a214  |
| isvalidlicense  | 0x569858  | 0x584658  | 0x56da54  | 0x56da68  | 0x54d538  | 0x54d540  | 0x54d568  | 0x549534  | 0x54a4f4  |
| ret_notify2     | 0x56b206  | 0x586008  | 0x56f440  | 0x56f430  | 0x54ef20  | 0x54ef3e  | 0x54ef4c  | 0x54af28  | 0x54bec6  |
| hosts string    | 0xce13c   | 0xce0ec   | 0xcef5c   | 0xcef5c   | 0xcf39c   | 0xcf39c   | 0xcf39c   | —         | —         |
| valid return    | 0         | 0         | 0x118     | 1         | 0         | 0         | 1         | 280      | 280       |

The offsets jump around freely (4199-4202 cluster near 0x55-0x58, 4203-4205 near
0x53-0x54), which is exactly why nothing is hardcoded -- every site is resolved
by structure. The "valid return" row shows the convention is not monotonic in the
build number: 4202 already returns 1, and 4201 is the lone magic-value build
(0x118). Note: `0x118` == `280` decimal -- the 4201 "magic value" and the
4206/4207 "280" convention are the SAME integer, emitted as the byte-identical
payload `b8 18 01 00 00 c3 90 90`.

## Patch payload (size-preserving, fixed 8-byte slot at IsValidLicense)

- valid==1: `48 31 c0 48 ff c0 c3 90` (xor rax,rax; inc rax; ret; nop).
- valid==0: `48 31 c0 c3 90 90 90 90` (xor rax,rax; ret; nop*4).
- any other value (e.g. 4201's 0x118): `b8 <imm32> c3 90 90`
  (`mov eax,imm32; ret; nop*2`). For 0x118 this is `b8 18 01 00 00 c3 90 90`.

The 0/1 cores are kept byte-exact so the proven recipes still reproduce; the
`mov eax,imm32` form (6 bytes) also fits the 8-byte slot.

The 8-byte slot matches the hand-verified 4205 recipe exactly, so the
build-agnostic path reproduces the proven md5s:

- 4205, S1..S5: `4eec4c3506773e9899cdbe8e463ab9c0`
- 4205, S1..S5 + hosts: `b2ad2138435a548bbe7093a5807bba30`

4204 has no prior ground-truth md5; it is validated by post-patch
self-verification plus a real isolated run (both plugin hosts spawn, main window
opens, no `(UNREGISTERED)` title, no license nag).

## Validation

`uv run st4patch --src <binary> --locate` reports the five offsets and the
inferred valid-return value for any supported build; on 4205 it additionally
prints `LOCATE: MATCH` against the reference SITES. The pytest suite unit-tests
the caller-fingerprint finder and both payloads on synthetic buffers (no binary
required), and regression-checks the 4205 md5s when the clean blob is present.

## Network hardening (`--no-update`, `--no-crash`)

Both flags redirect a phone-home host string to `127.0.0.1` (NUL-padded to the
original length, so size-preserving), which stops the request reaching Sublime's
servers -- not merely the user-visible popup. There are three copies of
`www.sublimetext.com` in the binary; only the right one is touched.

### `--no-update`

Non-latest builds show an "Update Available" popup on startup. The updater
resolves a dedicated host copy, then GETs a channel-specific relative path:

    /updates/4/dev_update_check?version=<build>&platform=linux&arch=x64

Two redirects, both build-agnostic:

1. **Host.** The updater's `www.sublimetext.com` copy is the one immediately
   preceded by the `latest_version` label
   (`find_update_host` anchors on `latest_version\0www.sublimetext.com\0`,
   count == 1). It is rewritten to `127.0.0.1`. The OTHER two copies --
   `https://www.sublimetext.com/buy` and the `sales@sublimetext.com` reissue
   text -- are deliberately left intact. (An earlier note that the host was
   "shared, so untouched" was wrong: the update host is a dedicated copy and IS
   redirected; only Buy/reissue are shared and left alone.)
2. **Path.** Only the channel-appropriate path variant is compiled in (dev builds
   carry `dev_update_check`, stable `stable_update_check`), so the substring
   `_update_check?version` is unique (count == 1). `find_update_path` anchors on
   it and walks back to the nearest `/updates/`, which is rewritten to
   `/dev/null` -- a 404 route, as defense-in-depth.

### `--no-crash`

The bundled `crash_handler` (a Crashpad binary) uploads minidumps to
`https://crash-server.sublimehq.com/api/upload` on a crash. `--no-crash` rewrites
the host `crash-server.sublimehq.com` (unique, count == 1) to `127.0.0.1`, so the
upload never leaves the machine. Sublime also starts fine if `crash_handler` is
made non-executable (`chmod a-x`), but the in-binary redirect travels with the
patched binary and needs no extra filesystem step.

### Per-build offsets (differ by build, so located dynamically)

| string                       | 4199     | 4200     | 4201     | 4202     | 4203     | 4204     | 4205     | 4206     | 4207     |
|------------------------------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| update host (latest_version) | 0xee533  | 0xee477  | 0xef339  | 0xef339  | 0xefc39  | 0xefc39  | 0xefc46  | —        | —        |
| update path (/updates/)      | 0xe3db7  | 0xf9559  | 0xd47d3  | 0xec402  | 0xd28ad  | 0xe9946  | 0xe52c4  | —        | —        |
| crash host                   | 0xdb169  | 0xdb0ee  | 0xdc00d  | 0xdbfde  | 0xdc674  | 0xdc633  | 0xdc633  | —        | —        |

The update-path offset swings wildly across builds (0xd28ad to 0xf9559),
underscoring why the path is located dynamically off the unique
`_update_check?version` anchor rather than by any fixed offset.

> Table note: a "—" in the network-string rows (e.g. 4206/4207) means the offset
> is **unrecorded, not absent** -- the `latest_version`, `_update_check?version`,
> and `crash-server.sublimehq.com` strings DO exist in the 4206/4207 binaries;
> they simply were not pinned per build, since the hosts are located dynamically
> by anchor.

For licensed users, Sublime also honors `"update_check": false` in
`Packages/User/Preferences.sublime-settings`; since a license-patched binary
appears licensed, that setting is a complementary user-space option, while
`--no-update` is the binary-level, settings-independent equivalent.

## Validated builds

| build | valid | clean md5                          | license recipe md5                 | fully-hardened recipe md5          |
|-------|-------|------------------------------------|------------------------------------|------------------------------------|
| 4199  | 0     | e9b5fcaba01db4d7ddca7b61b0816fc1   | 45ab9eda9d0f75e9da9e9ac9532837d3   | f0c8cd7e00e41fa184e9a6e616e60f1e   |
| 4200  | 0     | 2de36b6755ac192ba0970bebcecf6c40   | 2d5f5920496b6992fbe28551fd82f79e   | 2a5ede2cd3ec57c9a0728046c2550bd7   |
| 4201  | 0x118 | ef601b774d0f845e5fb924b7f7d0cbda   | 781f63ea9353d5282c2fda4126d74059   | bef7e0cce0083090826089648cd0cfaf   |
| 4202  | 1     | 20470c89374eda4df1d8307c6e5b11c2   | dd3593fb9e10bb2233612b7bf36749a5   | 2f0cebfcc888be6a8f7d847b5f97b835   |
| 4203  | 0     | 04ceb353faa23db3bf452988e61c0cfe   | 3c3cddce0118eeaddf2a8256ec189eb1   | af4b0721ab51d6672e2ff999c42bfcdb   |
| 4204  | 0     | 2b330244b229185fe593de61e7713f4a   | (see locator output)               | (see locator output)               |
| 4205  | 1     | c7539dda818f0c3537ba6cfa0f872fa9   | 4eec4c3506773e9899cdbe8e463ab9c0   | (with --hosts: b2ad2138..)         |
| 4206  | 280    | edd8e1c2e77d7b4cb3fdeae692965b0a | cb7cd5e3bb3464d2ea271a6ea6911461   | —                                  |
| 4207  | 280   | 4c62e941aeb0026cc5037541ed05cf0a   | 8bbf5d5873d64484aecd9f56c8abb4f0   | 592ae21abd442d6659827aedaaf2e94d   |

Nine builds, one algorithm. 4199/4200/4202/4203/4204/4205/4206/4207 each needed **zero**
code changes (4200 = stable channel, 4202 = early valid==1, 4199 = the oldest dev
build tested and absorbed with no adjustment at all). **4201 was the only build
that ever forced a code change**: its IsValidLicense returns the status code
0x118 (callers `cmp eax,0x118; sete`), so `_caller_convention` was generalized to
read any compare immediate and `isval_payload` to emit `mov eax,imm32; ret` for
non-0/1 values -- and that generalization is what then absorbed 4199 for free.
Each build patches + self-verifies under `--hosts --no-update --no-crash`; 4199
and 4201 additionally passed a real isolated launch (both plugin hosts, clean
window, no `(UNREGISTERED)` nag). Known clean md5s are advisory-only in
`constants.KNOWN_CLEAN_MD5`; patching never requires a match.

## Battery test: descending sweep and the 4176 floor

A descending battery (locate + patch + self-verify per build) ran from 4198 down
until the first structural failure. **Every downloadable build 4176-4207 passes**
(31 builds; 4179 is absent from the CDN (HTTP 404) so 31 of the 32-wide range were
actually fetched and tested -- a hosting gap, not a patcher limit). Below 4202 the
valid convention is 0 except 4201 (0x118); full clean md5s recorded in
`KNOWN_CLEAN_MD5`. The sweep added 4176-4198 with **zero** code changes.

**Roadblock: 4175.** The locator fails with "ret-notify signature not unique
(0 hits)". Root cause: both notify-function prologues were recompiled across the
4176 -> 4175 boundary, so the hand-pinned byte signatures miss:

| anchor                      | 4176 | 4175 | 4170 | 4160 | 4150 | 4126 | 4107 |
|-----------------------------|------|------|------|------|------|------|------|
| `SIG_NOP_CONST` (nop)       | 1    | 1    | 1    | 1    | 1    | 1    | 1    |
| `SIG_RET_NOTIFY1` full      | 1    | 0    | 0    | 0    | 0    | 0    | 0    |
| `SIG_RET_NOTIFY2` full      | 1    | 0    | 0    | 0    | 0    | 0    | 0    |
| notify1 prologue *prefix*   | 111  | 121  | 118  | 133  | 125  | 133  | 128  |
| notify2 prologue *prefix*   | 6    | 1    | 1    | 0    | 0    | 1    | 1    |

The "prefix" rows drop the build-variant immediate (notify1's `sub rsp,<imm>`,
notify2's trailing constant) and keep only the stable register-shape bytes. Two
facts make 4175 a genuine break, not a 4201-style immediate tweak:

1. **notify1's stable prefix is hopelessly generic** (111-133 functions share
   `push r15,r14,r12,rbx; sub rsp,...`), so it cannot anchor the function on its
   own; the old 12-byte signature was unique only because it pinned the exact
   frame size `0x308`, which changed.
2. **notify2's prologue shape itself changed** -- on 4150/4160 the structural
   prefix has **0** hits, meaning those notify functions were recompiled with
   different register allocation, not merely a different constant.

Both notify anchors hold at 4176 and die at 4175, staying dead all the way down
to 4107. So 4175 is a clean **era boundary**: builds >=4176 are one binary era;
builds <=4175 are an older era where the notify functions need a structural
locator (the way `_locate_isvalidlicense` replaced the 4205-only IsValidLicense
byte signature). The nop anchor and the valid==0 convention survive the boundary;
only the two notify prologues break. Supporting 4175 and below is deferred future
work -- it requires new structural anchors for both notify functions, possibly
per sub-era.

### Confirmed support window

| range       | status                                                          |
|-------------|-----------------------------------------------------------------|
| 4176 - 4207 | validated build-agnostic (4179 missing on CDN, not a limit)     |
| <= 4175     | roadblock: notify-prologue signatures recompiled (era boundary) |
