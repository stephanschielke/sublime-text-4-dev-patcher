#!/usr/bin/env python3
"""Sublime Text Build 4205 (Linux x64 ELF) license patcher - CLI entry point.

Owner-authorized, for plugin-development testing on the owner's own installed copy.
Patches a USER-OWNED COPY by default; the cp into /opt is a separate sudo step.

PROVEN RECIPE (PATCH-4205-A): the Linux Build 4200 recipe
(gist github.com/maboloshi/feaa63c35f4c2baab24c9aaf9b3f4e47, comment 5597063)
ported to 4205, with IsValidLicense returning the 4205 valid enum value of **1**
(not 0). See research/sources-and-version-map.md for the full source map and
the EXP-VTABLE / EXP-RET0 / EXP-RET1 experiment vocabulary.

Why return 1: every caller of IsValidLicense (VA 0x54e568) does `cmp eax, 1` and
treats 1 as "valid" (two of them also do `sete byte[rdi+5]`). The 4200 recipe used
`mov rax,0` (EXP-RET0); the github.com/rainbowpigeon/sublime-text-4-patcher
architecture switches to "ret1" for builds >= 4205 (EXP-RET1). Confirmed by
disassembling all four call sites.

Patch sites (fileoff; .text VA = fileoff + 0x1000) and recipe md5s live in
st4patcher/constants.py.

Usage:
  st4patch --src /opt/sublime_text/sublime_text --out /tmp/sublime_text.patched [--hosts]
  st4patch --src ... --verify-only [--hosts]
  st4patch --src ... --locate
  # then: sudo cp /tmp/sublime_text.patched /opt/sublime_text/sublime_text
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from st4patcher.constants import CLEAN_MD5, SITES
from st4patcher.patcher import apply_located, md5, report, verify_located


def _load_locator():
    try:
        from st4patcher.locate_sites import locate

        return locate
    except ImportError as exc:
        raise SystemExit(f"locate needs locate_sites + capstone: {exc}") from exc


def _run_locate(raw: bytes) -> int:
    """Structurally locate the sites for ANY build; cross-check vs 4205 SITES."""
    res = _load_locator()(raw)
    print("structurally-located offsets:")
    for name in ("nop1", "nop2", "ret_notify1", "isvalidlicense", "ret_notify2"):
        print(f"  {name:18s} fileoff={hex(res.sites[name])}")
    print(f"  IsValidLicense valid-return value: {res.isval_valid_value}")

    hard = {name: off for name, off, _o, _n in SITES}
    name_map = {
        "nop1_revalidate_cb": "nop1",
        "nop2_revalidate_cb": "nop2",
        "ret_notify1": "ret_notify1",
        "isvalidlicense_ret1": "isvalidlicense",
        "ret_notify2": "ret_notify2",
    }
    if all(res.sites.get(name_map[n]) == off for n, off in hard.items()):
        print("LOCATE: MATCH (offsets equal the 4205 reference SITES)")
    else:
        print("LOCATE: this build differs from 4205 reference; using located offsets")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="st4patch", description="Sublime 4205 Linux patcher (proven recipe PATCH-4205-A)")
    ap.add_argument("--src", required=True, help="source binary (e.g. /opt/sublime_text/sublime_text)")
    ap.add_argument("--out", help="output patched binary path")
    ap.add_argument("--hosts", action="store_true", help="also apply in-binary phone-home block")
    ap.add_argument(
        "--no-update",
        dest="no_update",
        action="store_true",
        help="disable the auto-updater (redirect its host to 127.0.0.1 + its path to a 404 route)",
    )
    ap.add_argument(
        "--no-crash",
        dest="no_crash",
        action="store_true",
        help="disable crash-report upload (redirect crash-server host to 127.0.0.1)",
    )
    ap.add_argument("--verify-only", action="store_true", help="report signature presence, patch nothing")
    ap.add_argument(
        "--locate",
        action="store_true",
        help="resolve patch offsets by byte SIGNATURE (version-resilient) "
        "and cross-check them against the hardcoded SITES offsets",
    )
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_file():
        raise SystemExit(f"src not found: {src}")
    raw = src.read_bytes()
    print(f"src: {src}\n  size={len(raw)} md5={md5(raw)}")
    if md5(raw) != CLEAN_MD5:
        print(f"  WARNING: src md5 != clean 4205 ({CLEAN_MD5}); proceeding by signature.")

    if args.locate:
        return _run_locate(raw)

    if args.verify_only:
        ok = report(raw, args.hosts)
        print("VERIFY:", "PASS" if ok else "FAIL")
        return 0 if ok else 2

    if not args.out:
        raise SystemExit("--out is required unless --verify-only")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    bak = out.with_suffix(out.suffix + ".src.bak")
    bak.write_bytes(raw)
    print(f"backup(src) -> {bak}")

    res = _load_locator()(raw)
    print("located sites:")
    for name in ("nop1", "nop2", "ret_notify1", "isvalidlicense", "ret_notify2"):
        print(f"  {name:18s} fileoff={hex(res.sites[name])}")
    print(f"  IsValidLicense valid-return value: {res.isval_valid_value}")

    data = bytearray(raw)
    log = apply_located(data, res.sites, res.isval_valid_value, args.hosts, args.no_update, args.no_crash)
    assert len(data) == len(raw), "size changed! refusing"

    fails = verify_located(bytes(data), res.sites, res.isval_valid_value, args.hosts, args.no_update, args.no_crash)
    if fails:
        for f in fails:
            print("  SELF-VERIFY FAIL:", f)
        raise SystemExit("ABORT: post-patch self-verification failed; not writing output.")

    out.write_bytes(bytes(data))
    print("patches applied:")
    for line in log:
        print("  -", line)
    print("self-verify: PASS")
    print(f"out: {out}\n  size={len(data)} md5={md5(bytes(data))}")
    print("\nNext (sudo):")
    print(f"  pkill sublime_text; sudo cp '{out}' /opt/sublime_text/sublime_text && subl")
    print("  # manual verification: the patched test copy reaches the normal main-window startup path")
    print("  # restore: sudo cp binaries/clean-original/4205-linux-amd64/sublime_text /opt/sublime_text/sublime_text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
