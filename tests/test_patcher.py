from pathlib import Path

import pytest

from st4patcher.constants import (
    CLEAN_MD5,
    CRASH_HOST,
    HOSTS_NEW,
    HOSTS_OLD,
    SITE_TO_LOCATE_KEY,
    SITES,
    UPDATE_HOST,
    UPDATE_HOST_ANCHOR,
    isval_payload,
    loopback_for,
)
from st4patcher.locate_sites import find_all, locate
from st4patcher.patcher import (
    apply_located,
    apply_patches,
    find_update_host,
    find_update_path,
    md5,
    report,
    verify_located,
)

UPDATE_PATH = b"/updates/4/dev_update_check?version=4205&platform=linux&arch=x64"

CLEAN = Path("binaries/clean-original/4205-linux-amd64/sublime_text")


def make_clean_buffer() -> bytearray:
    end = max(off + len(old) for _name, off, old, _new in SITES)
    hosts_end = 0xCF39C + len(HOSTS_OLD)
    data = bytearray(max(end, hosts_end))
    for _name, off, old, _new in SITES:
        data[off : off + len(old)] = old
    data[0xCF39C : 0xCF39C + len(HOSTS_OLD)] = HOSTS_OLD
    return data


class TestMd5:
    def test_known_vector_empty_bytes(self) -> None:
        assert md5(b"") == "d41d8cd98f00b204e9800998ecf8427e"


class TestFindAll:
    def test_empty_data(self) -> None:
        assert find_all(b"", b"a") == []

    def test_single_match(self) -> None:
        assert find_all(b"abc", b"b") == [1]

    def test_multiple_matches(self) -> None:
        assert find_all(b"banana", b"an") == [1, 3]

    def test_overlapping_matches(self) -> None:
        assert find_all(b"aaaa", b"aa") == [0, 1, 2]

    def test_not_found(self) -> None:
        assert find_all(b"abc", b"z") == []


class TestApplyPatches:
    def test_apply_patches_rewrites_all_sites_and_hosts(self) -> None:
        data = make_clean_buffer()
        size_before = len(data)

        log = apply_patches(data, with_hosts=True)

        assert len(log) == 6
        assert len(data) == size_before
        for name, off, _old, new in SITES:
            assert bytes(data[off : off + len(new)]) == new, name
        assert bytes(data[0xCF39C : 0xCF39C + len(HOSTS_NEW)]) == HOSTS_NEW

    def test_apply_patches_idempotent_on_already_patched_buffer(self) -> None:
        data = make_clean_buffer()
        apply_patches(data, with_hosts=True)

        log = apply_patches(data, with_hosts=True)

        assert len(log) == 6
        assert sum("already patched, skip" in line for line in log) == 6

    def test_apply_patches_raises_on_unrecognized_site_head(self) -> None:
        data = make_clean_buffer()
        name, off, old, _new = SITES[0]
        data[off] = 0x00 if old[0] != 0x00 else 0xFF

        with pytest.raises(SystemExit, match=rf"ABORT: {name}"):
            apply_patches(data, with_hosts=False)


class TestReport:
    def test_report_true_on_synthetic_clean_buffer(self, capsys: pytest.CaptureFixture[str]) -> None:
        ok = report(bytes(make_clean_buffer()), with_hosts=True)

        captured = capsys.readouterr()
        assert ok is True
        assert "[CLEAN]" in captured.out
        assert "[OK] hosts" in captured.out

    def test_report_false_on_corrupted_site(self, capsys: pytest.CaptureFixture[str]) -> None:
        data = make_clean_buffer()
        _name, off, old, _new = SITES[0]
        data[off] = 0x00 if old[0] != 0x00 else 0xFF

        ok = report(bytes(data), with_hosts=False)

        captured = capsys.readouterr()
        assert ok is False
        assert "[MISMATCH]" in captured.out


LOCATED_SITES = {
    "nop1": 0x10,
    "nop2": 0x20,
    "ret_notify1": 0x30,
    "isvalidlicense": 0x40,
    "ret_notify2": 0x60,
}
HOSTS_AT = 0x100


UPDATE_AT = 0x140
UHOST_AT = 0x200
CRASH_AT = 0x280
UHOST_OFF = UHOST_AT + len(b"latest_version\x00")


def make_located_clean() -> bytearray:
    data = bytearray(CRASH_AT + len(CRASH_HOST) + 4)
    for key in ("nop1", "nop2"):
        data[LOCATED_SITES[key] : LOCATED_SITES[key] + 5] = b"\xe8\x11\x22\x33\x44"
    for key in ("ret_notify1", "ret_notify2"):
        data[LOCATED_SITES[key]] = 0x41
    data[LOCATED_SITES["isvalidlicense"] : LOCATED_SITES["isvalidlicense"] + 8] = b"\x55" * 8
    data[HOSTS_AT : HOSTS_AT + len(HOSTS_OLD)] = HOSTS_OLD
    data[UPDATE_AT : UPDATE_AT + len(UPDATE_PATH)] = UPDATE_PATH
    data[UHOST_AT : UHOST_AT + len(UPDATE_HOST_ANCHOR)] = UPDATE_HOST_ANCHOR
    data[CRASH_AT : CRASH_AT + len(CRASH_HOST)] = CRASH_HOST
    return data


class TestApplyLocated:
    def test_apply_located_ret1_with_hosts(self) -> None:
        data = make_located_clean()
        size_before = len(data)

        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=True)

        assert len(data) == size_before
        for key in ("nop1", "nop2"):
            assert bytes(data[LOCATED_SITES[key] : LOCATED_SITES[key] + 5]) == b"\x90" * 5
        for key in ("ret_notify1", "ret_notify2"):
            assert data[LOCATED_SITES[key]] == 0xC3
        off = LOCATED_SITES["isvalidlicense"]
        assert bytes(data[off : off + 8]) == isval_payload(1)
        assert bytes(data[HOSTS_AT : HOSTS_AT + len(HOSTS_NEW)]) == HOSTS_NEW
        assert verify_located(bytes(data), LOCATED_SITES, valid_value=1, with_hosts=True) == []

    def test_apply_located_ret0(self) -> None:
        data = make_located_clean()

        apply_located(data, LOCATED_SITES, valid_value=0, with_hosts=False)

        off = LOCATED_SITES["isvalidlicense"]
        assert bytes(data[off : off + 8]) == isval_payload(0)
        assert verify_located(bytes(data), LOCATED_SITES, valid_value=0, with_hosts=False) == []

    def test_verify_located_detects_corrupted_nop(self) -> None:
        data = make_located_clean()
        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=False)
        data[LOCATED_SITES["nop1"]] = 0x00

        fails = verify_located(bytes(data), LOCATED_SITES, valid_value=1, with_hosts=False)

        assert any("nop1" in f for f in fails)

    def test_verify_located_detects_wrong_convention(self) -> None:
        data = make_located_clean()
        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=False)

        fails = verify_located(bytes(data), LOCATED_SITES, valid_value=0, with_hosts=False)

        assert any("isvalidlicense" in f for f in fails)


class TestUpdateBlock:
    def test_find_update_path_anchors_on_marker(self) -> None:
        data = make_located_clean()
        assert find_update_path(data) == UPDATE_AT

    def test_find_update_host_anchors_on_label(self) -> None:
        data = make_located_clean()
        assert find_update_host(data) == UHOST_OFF

    def test_find_update_path_absent_returns_minus_one(self) -> None:
        assert find_update_path(b"\x00" * 64) == -1

    def test_find_update_host_absent_returns_minus_one(self) -> None:
        assert find_update_host(b"\x00" * 64) == -1

    def test_apply_located_redirects_update_host_and_path(self) -> None:
        data = make_located_clean()

        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=False, with_update_block=True)

        assert data.find(b"/updates/4/dev") < 0
        assert bytes(data[UPDATE_AT : UPDATE_AT + 9]) == b"/dev/null"
        assert bytes(data[UHOST_OFF : UHOST_OFF + len(UPDATE_HOST)]) == loopback_for(UPDATE_HOST)
        assert find_update_path(data) < 0
        assert verify_located(bytes(data), LOCATED_SITES, valid_value=1, with_hosts=False, with_update_block=True) == []

    def test_verify_located_detects_live_update_path(self) -> None:
        data = make_located_clean()
        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=False, with_update_block=False)

        fails = verify_located(bytes(data), LOCATED_SITES, valid_value=1, with_hosts=False, with_update_block=True)

        assert any("update" in f for f in fails)


class TestCrashBlock:
    def test_apply_located_redirects_crash_host(self) -> None:
        data = make_located_clean()

        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=False, with_crash_block=True)

        assert data.find(CRASH_HOST) < 0
        assert bytes(data[CRASH_AT : CRASH_AT + len(CRASH_HOST)]) == loopback_for(CRASH_HOST)
        assert verify_located(bytes(data), LOCATED_SITES, valid_value=1, with_hosts=False, with_crash_block=True) == []

    def test_verify_located_detects_live_crash_host(self) -> None:
        data = make_located_clean()
        apply_located(data, LOCATED_SITES, valid_value=1, with_hosts=False, with_crash_block=False)

        fails = verify_located(bytes(data), LOCATED_SITES, valid_value=1, with_hosts=False, with_crash_block=True)

        assert any("crash" in f for f in fails)


class TestLoopbackFor:
    def test_pads_to_host_length(self) -> None:
        out = loopback_for(b"www.sublimetext.com")
        assert out == b"127.0.0.1" + b"\x00" * (19 - 9)
        assert len(out) == 19

    def test_raises_when_host_shorter_than_loopback(self) -> None:
        with pytest.raises(ValueError, match="shorter"):
            loopback_for(b"x.io")


class TestBinaryDependent:
    @pytest.mark.skipif(not CLEAN.exists(), reason="clean 4205 binary absent")
    def test_clean_binary_md5_matches_constant(self) -> None:
        assert md5(CLEAN.read_bytes()) == CLEAN_MD5

    @pytest.mark.skipif(not CLEAN.exists(), reason="clean 4205 binary absent")
    def test_locate_matches_hardcoded_site_offsets(self) -> None:
        clean = CLEAN.read_bytes()
        found = locate(clean)
        expected = {SITE_TO_LOCATE_KEY[name]: off for name, off, _old, _new in SITES}

        assert found.sites == expected
        assert found.isval_valid_value == 1

    @pytest.mark.skipif(not CLEAN.exists(), reason="clean 4205 binary absent")
    def test_full_patch_recipe_matches_expected_md5(self) -> None:
        from st4patcher.constants import RECIPE_MD5

        data = bytearray(CLEAN.read_bytes())

        apply_patches(data, with_hosts=False)

        assert md5(bytes(data)) == RECIPE_MD5["PATCH-4205-A"]
