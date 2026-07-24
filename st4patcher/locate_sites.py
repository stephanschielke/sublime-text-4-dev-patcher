"""Build-agnostic locator for the Sublime Text 4 (Linux x64) license patch sites.

Instead of hardcoding file offsets (which change every build), this module finds
each patch site by structure and recovers, in one pass, the five offsets the
patcher needs plus the build's IsValidLicense "valid" return value.

Four of the five sites are found by stable, build-invariant byte signatures
(unique in every build observed): the two revalidation NOP calls (anchored on
``mov edx,0x1388``) and the two notify-function prologues.

The fifth site, IsValidLicense, is the one that drifts between builds: the exact
``cmp eax,1; sete [rdi+5]`` idiom the old locator keyed on is 4205-specific. It
is found here by a CALLER FINGERPRINT instead:

    1. The license gate sits in a tight cluster bounded by the two notify
       prologues. We scan E8 rel32 calls whose target lands in that window.
    2. IsValidLicense is the function whose >=2 callers each, within a few
       instructions of the call, compare EAX and store the result with
       ``sete [reg+disp8]`` (the license-registered-flag write).
    3. The caller compare also reveals the convention: ``cmp eax, <imm>`` means
       the valid return value is that immediate (1 on 4202/4205, the status code
       0x118 on 4201); ``test eax,eax`` means it is 0 (4200/4203/4204). The
       patcher emits the matching return stub (``mov eax,imm32; ret`` for values
       other than 0/1).

This recovers 4200..4205 with a single algorithm, including 4201's magic-value
convention, with no per-build code.

Requires: capstone (declared in pyproject.toml).
"""

from __future__ import annotations

import contextlib
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from st4patcher.constants import (
    SIG_NOP_CONST,
    SIG_RET_NOTIFY1,
    SIG_RET_NOTIFY2,
    VA_BIAS,
)

try:
    import capstone
    from capstone import x86
except ImportError:  # pragma: no cover
    print("ERROR: capstone is required (pip install capstone).", file=sys.stderr)
    raise


ISVAL_PROLOGUE = bytes.fromhex("5541574156415541")  # push rbp,r15,r14,r13,r12; ...
SITE_ORDER = ["nop1", "nop2", "ret_notify1", "isvalidlicense", "ret_notify2"]


@dataclass(frozen=True)
class LocateResult:
    """Resolved patch sites for one binary, plus the IsValidLicense convention.

    ``sites`` maps each locate key to a file offset. ``isval_valid_value`` is the
    integer the build's callers treat as "valid" (0 or 1), driving the S4 patch.
    """

    sites: dict[str, int]
    isval_valid_value: int


def _md() -> capstone.Cs:
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    return md


def find_all(data: bytes, pat: bytes) -> list[int]:
    """Return every start offset where ``pat`` occurs in ``data``."""
    out: list[int] = []
    i = 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            return out
        out.append(j)
        i = j + 1


_find_all = find_all


def _e8_calls_into(data: bytes, lo: int, hi: int) -> dict[int, list[int]]:
    """Group E8 rel32 call sites by target, keeping only targets in [lo, hi)."""
    by_target: dict[int, list[int]] = {}
    i = 0
    n = len(data)
    while True:
        i = data.find(b"\xe8", i)
        if i < 0 or i + 5 > n:
            break
        rel = int.from_bytes(data[i + 1 : i + 5], "little", signed=True)
        target = (i + 5) + rel
        if lo <= target < hi:
            by_target.setdefault(target, []).append(i)
        i += 1
    return by_target


def _caller_convention(md, data: bytes, call_off: int, span: int = 0x16) -> int | None:
    """Inspect the bytes right after a call for the license-flag store idiom.

    Returns the integer the caller treats as "valid": the immediate of a
    ``cmp eax, <imm>`` (e.g. 1 on 4205, 0x118 on 4201), or 0 for the bare
    ``test eax, eax`` form. Returns None when the caller stores no
    ``sete [reg+disp]`` flag or compares EAX in neither recognised way.
    """
    cmp_imm: int | None = None
    saw_test = saw_sete = False
    start = call_off + 5
    for ins in md.disasm(data[start : start + span], start + VA_BIAS):
        if ins.mnemonic == "cmp" and ins.op_str.startswith("eax, ") and cmp_imm is None:
            with contextlib.suppress(ValueError):
                cmp_imm = int(ins.op_str.split(",", 1)[1].strip(), 0)
        elif ins.mnemonic == "test" and ins.op_str == "eax, eax":
            saw_test = True
        elif ins.mnemonic == "sete":
            saw_sete = True
    if not saw_sete or not (cmp_imm is not None or saw_test):
        return None
    return cmp_imm if cmp_imm is not None else 0


def _locate_isvalidlicense(md, data: bytes, ret1: int, ret2: int) -> tuple[int, int]:
    """Find IsValidLicense in the notify-bounded cluster by caller fingerprint.

    Returns (fileoff, valid_value). Raises SystemExit if zero or several
    functions match the fingerprint (ambiguity is reported, never guessed).
    """
    lo, hi = min(ret1, ret2), max(ret1, ret2) + 0x100
    candidates: list[tuple[int, int]] = []
    for target, callers in _e8_calls_into(data, lo, hi).items():
        if len(callers) < 2:
            continue
        votes = [v for v in (_caller_convention(md, data, c) for c in callers) if v is not None]
        if not votes:
            continue
        if data[target : target + len(ISVAL_PROLOGUE)] != ISVAL_PROLOGUE:
            continue
        winner = Counter(votes).most_common(1)[0][0]
        candidates.append((target, winner))
    if not candidates:
        raise SystemExit(
            "locate: no IsValidLicense candidate found in the license cluster "
            "(callers may use vtable dispatch; build unsupported by this finder)."
        )
    if len(candidates) > 1:
        listing = ", ".join(f"0x{off:x}(valid={v})" for off, v in candidates)
        raise SystemExit(f"locate: ambiguous IsValidLicense candidates: {listing}")
    return candidates[0]


def locate(data: bytes) -> LocateResult:
    """Resolve all five patch sites and the IsValidLicense convention, or raise."""
    md = _md()
    sites: dict[str, int] = {}

    for name, sig in (("ret_notify1", SIG_RET_NOTIFY1), ("ret_notify2", SIG_RET_NOTIFY2)):
        hits = find_all(data, sig)
        if len(hits) != 1:
            raise SystemExit(f"locate: {name} signature not unique ({len(hits)} hits)")
        sites[name] = hits[0]

    anchors = find_all(data, SIG_NOP_CONST)
    if len(anchors) != 1:
        raise SystemExit(f"locate: nop anchor not unique ({len(anchors)} hits)")
    nop1 = anchors[0] + 5
    tgt = None
    for ins in md.disasm(data[nop1 : nop1 + 5], nop1 + VA_BIAS):
        if ins.mnemonic == "call":
            tgt = ins.operands[0].imm
    nop2 = None
    scan = nop1 + 5
    for ins in md.disasm(data[scan : scan + 0x40], scan + VA_BIAS):
        if (
            ins.mnemonic == "call"
            and ins.operands
            and ins.operands[0].type == x86.X86_OP_IMM
            and ins.operands[0].imm == tgt
        ):
            nop2 = ins.address - VA_BIAS
            break
    if data[nop1] != 0xE8 or nop2 is None or data[nop2] != 0xE8:
        raise SystemExit("locate: nop1/nop2 did not resolve to call (E8) opcodes")
    sites["nop1"] = nop1
    sites["nop2"] = nop2

    isval_off, valid_value = _locate_isvalidlicense(md, data, sites["ret_notify1"], sites["ret_notify2"])
    sites["isvalidlicense"] = isval_off

    return LocateResult(sites=sites, isval_valid_value=valid_value)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <sublime_text binary>", file=sys.stderr)
        return 2
    data = Path(sys.argv[1]).read_bytes()
    res = locate(data)
    print(f"located {len(res.sites)} sites in {sys.argv[1]}:")
    for name in SITE_ORDER:
        print(f"  {name:18s} fileoff={hex(res.sites[name])}  byte={data[res.sites[name]]:02x}")
    print(f"  IsValidLicense valid-return value: {res.isval_valid_value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
