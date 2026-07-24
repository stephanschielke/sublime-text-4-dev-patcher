"""Pure-logic patch primitives for the license recipe.

None of these functions need capstone or a real binary beyond the bytes you
hand them, so they are directly unit-testable. The structural locate path (which
does need capstone) lives in st4patcher.locate_sites; this module consumes the
offsets it returns.

``report`` / ``apply_patches`` operate on the hardcoded 4205 ``SITES`` (used by
``--verify-only`` and regression). ``apply_located`` / ``verify_located`` are the
build-agnostic path: they take offsets resolved at runtime and the inferred
IsValidLicense convention, so they patch any supported build.
"""

from __future__ import annotations

import hashlib

from st4patcher.constants import (
    CRASH_HOST,
    HOSTS_NEW,
    HOSTS_OFF,
    HOSTS_OLD,
    NOP_CALL,
    RET,
    SITES,
    UPDATE_HOST,
    UPDATE_HOST_ANCHOR,
    UPDATE_PATH_KILL,
    UPDATE_PATH_MARK,
    UPDATE_PATH_PREFIX,
    isval_payload,
    loopback_for,
)


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def report(data: bytes, with_hosts: bool) -> bool:
    """Print per-site CLEAN/PATCHED/MISMATCH status; return True if all recognized."""
    ok = True
    for name, off, old, new in SITES:
        head = bytes(data[off : off + len(old)])
        clean = head == old
        patched = head == new
        status = "CLEAN" if clean else ("PATCHED" if patched else "MISMATCH")
        print(f"[{status}] {name} @ {hex(off)}: have {head.hex()} want {old.hex()}")
        if not (clean or patched):
            ok = False
    if with_hosts:
        h = bytes(data[HOSTS_OFF : HOSTS_OFF + len(HOSTS_OLD)])
        good = h in (HOSTS_OLD, HOSTS_NEW)
        print(
            f"[{'OK' if good else 'WARN'}] hosts @ {hex(HOSTS_OFF)}: "
            f"{'clean' if h == HOSTS_OLD else ('patched' if h == HOSTS_NEW else 'unexpected')}"
        )
    return ok


def apply_patches(data: bytearray, with_hosts: bool) -> list[str]:
    """Apply all SITES (and optionally hosts) in place; return a change log.

    Raises SystemExit if a site's head matches neither the clean nor the
    already-patched bytes (i.e. the binary is not the expected 4205 layout).
    """
    log: list[str] = []
    for name, off, old, new in SITES:
        head = bytes(data[off : off + len(old)])
        if head == new:
            log.append(f"{name} @ {hex(off)}: already patched, skip")
            continue
        if head != old:
            raise SystemExit(
                f"ABORT: {name} @ {hex(off)} head {head.hex()} != {old.hex()}; "
                "binary is not the expected clean 4205 layout."
            )
        assert len(old) == len(new), f"{name}: length mismatch"
        data[off : off + len(new)] = new
        log.append(f"{name} @ {hex(off)}: {old.hex()} -> {new.hex()}")
    if with_hosts:
        h = bytes(data[HOSTS_OFF : HOSTS_OFF + len(HOSTS_OLD)])
        if h == HOSTS_OLD:
            data[HOSTS_OFF : HOSTS_OFF + len(HOSTS_NEW)] = HOSTS_NEW
            log.append(f"hosts @ {hex(HOSTS_OFF)}: '{HOSTS_OLD.decode()}' -> '127.0.0.1\\0..'")
        elif h == HOSTS_NEW:
            log.append(f"hosts @ {hex(HOSTS_OFF)}: already patched, skip")
    return log


def _patch_hosts(data: bytearray) -> int:
    """Neutralize the phone-home string in place; return its offset or -1."""
    i = data.find(HOSTS_OLD)
    if i < 0:
        if data.find(HOSTS_NEW) >= 0:
            return data.find(HOSTS_NEW)
        return -1
    data[i : i + len(HOSTS_NEW)] = HOSTS_NEW
    return i


def find_update_path(data: bytes | bytearray) -> int:
    """Offset of the channel update path's leading "/updates/", or -1.

    Anchored on the unique ``_update_check?version`` marker, then walked back to
    the nearest preceding ``/updates/`` so it works for dev and stable channels
    regardless of build.
    """
    mark = data.find(UPDATE_PATH_MARK)
    if mark < 0:
        return -1
    return data.rfind(UPDATE_PATH_PREFIX, 0, mark)


def find_update_host(data: bytes | bytearray) -> int:
    """Offset of the updater's dedicated host string, or -1.

    Anchored on the preceding ``latest_version`` label so it selects the updater
    copy of ``www.sublimetext.com`` and never the Buy/reissue copies.
    """
    anchor = data.find(UPDATE_HOST_ANCHOR)
    if anchor < 0:
        return -1
    return anchor + len(b"latest_version\x00")


def _redirect_host(data: bytearray, off: int, host: bytes) -> bool:
    """Overwrite ``host`` at ``off`` with NUL-padded loopback; return changed."""
    if bytes(data[off : off + len(host)]) != host:
        return False
    data[off : off + len(host)] = loopback_for(host)
    return True


def _patch_update(data: bytearray) -> list[str]:
    """Redirect the update host to loopback and the path to a 404; return a log."""
    log: list[str] = []
    h = find_update_host(data)
    if h >= 0 and _redirect_host(data, h, UPDATE_HOST):
        log.append(f"update host @ {hex(h)}: '{UPDATE_HOST.decode()}' -> '127.0.0.1\\0..'")
    p = find_update_path(data)
    if p >= 0:
        data[p : p + len(UPDATE_PATH_PREFIX)] = UPDATE_PATH_KILL
        log.append(f"update path @ {hex(p)}: '/updates/' -> '{UPDATE_PATH_KILL.decode()}' (404 route)")
    if not log:
        log.append("update: nothing to patch (no update strings in this build)")
    return log


def _patch_crash(data: bytearray) -> int:
    """Redirect the crash-report upload host to loopback; return its offset or -1."""
    i = data.find(CRASH_HOST)
    if i < 0:
        return -1
    _redirect_host(data, i, CRASH_HOST)
    return i


def apply_located(
    data: bytearray,
    sites: dict[str, int],
    valid_value: int,
    with_hosts: bool,
    with_update_block: bool = False,
    with_crash_block: bool = False,
) -> list[str]:
    """Apply all sites using runtime-resolved offsets; return a change log.

    Build-agnostic: ``sites`` comes from the locator and ``valid_value`` selects
    the IsValidLicense return stub. The two nop calls become NOPs, the two notify
    prologues become ``ret``, and IsValidLicense is rewritten to return the
    build's valid constant. ``with_update_block`` redirects the auto-updater host
    to loopback and its path to a 404 route; ``with_crash_block`` redirects the
    crash-report upload host to loopback.
    """
    log: list[str] = []
    for key in ("nop1", "nop2"):
        off = sites[key]
        data[off : off + len(NOP_CALL)] = NOP_CALL
        log.append(f"{key} @ {hex(off)}: call -> nop*5")
    for key in ("ret_notify1", "ret_notify2"):
        off = sites[key]
        data[off : off + 1] = RET
        log.append(f"{key} @ {hex(off)}: 0x41 -> 0xc3 (ret)")
    off = sites["isvalidlicense"]
    payload = isval_payload(valid_value)
    data[off : off + len(payload)] = payload
    log.append(f"isvalidlicense @ {hex(off)}: prologue -> return {valid_value} ({payload.hex()})")
    if with_hosts:
        h_off = _patch_hosts(data)
        if h_off >= 0:
            log.append(f"hosts @ {hex(h_off)}: '{HOSTS_OLD.decode()}' -> '127.0.0.1\\0..'")
    if with_update_block:
        log.extend(_patch_update(data))
    if with_crash_block:
        c_off = _patch_crash(data)
        if c_off >= 0:
            log.append(f"crash host @ {hex(c_off)}: '{CRASH_HOST.decode()}' -> '127.0.0.1\\0..'")
        else:
            log.append("crash host: NOT FOUND (no crash-server string in this build)")
    return log


def verify_located(
    data: bytes,
    sites: dict[str, int],
    valid_value: int,
    with_hosts: bool,
    with_update_block: bool = False,
    with_crash_block: bool = False,
) -> list[str]:
    """Self-check a patched buffer without any known-good md5; return failures.

    Confirms each nop site is ``90*5``, each notify byte is ``c3``,
    IsValidLicense matches the expected return stub, the phone-home string is
    gone (when requested), the live update host+path are gone (when requested),
    and the crash-report host is gone (when requested). An empty list means the
    patch is structurally correct.
    """
    fails: list[str] = []
    for key in ("nop1", "nop2"):
        off = sites[key]
        if bytes(data[off : off + len(NOP_CALL)]) != NOP_CALL:
            fails.append(f"{key} @ {hex(off)} not NOPed")
    for key in ("ret_notify1", "ret_notify2"):
        off = sites[key]
        if data[off] != 0xC3:
            fails.append(f"{key} @ {hex(off)} not 0xc3")
    off = sites["isvalidlicense"]
    want = isval_payload(valid_value)
    if bytes(data[off : off + len(want)]) != want:
        fails.append(f"isvalidlicense @ {hex(off)} stub mismatch")
    if with_hosts and data.find(HOSTS_OLD) >= 0:
        fails.append("hosts string still present")
    if with_update_block:
        if find_update_path(data) >= 0:
            fails.append("live update path still present")
        if (
            find_update_host(data) >= 0
            and bytes(data[find_update_host(data) : find_update_host(data) + len(UPDATE_HOST)]) == UPDATE_HOST
        ):
            fails.append("live update host still present")
    if with_crash_block and data.find(CRASH_HOST) >= 0:
        fails.append("crash-report host still present")
    return fails
