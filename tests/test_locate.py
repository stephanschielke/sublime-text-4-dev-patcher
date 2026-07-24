import pytest

from st4patcher.constants import SIG_RET_NOTIFY1, SIG_RET_NOTIFY2
from st4patcher.locate_sites import (
    ISVAL_PROLOGUE,
    _caller_convention,
    _locate_isvalidlicense,
    _md,
)

CMP1_IDIOM = bytes.fromhex("83f8010f944705")  # cmp eax,1 ; sete [rdi+5]
TEST_IDIOM = bytes.fromhex("85c00f94470c")  # test eax,eax ; sete [rdi+0xc]
CMP_MAGIC_IDIOM = bytes.fromhex("3d180100000f944705")  # cmp eax,0x118 ; sete [rdi+5] (4201)


def _e8(call_off: int, target: int) -> bytes:
    rel = target - (call_off + 5)
    return b"\xe8" + rel.to_bytes(4, "little", signed=True)


def _build(idiom: bytes) -> tuple[bytearray, int]:
    """Synthetic license cluster: two ret-notify anchors framing an IsValidLicense.

    Layout keeps the function target T strictly between the two notify
    signatures so it falls inside the window _locate_isvalidlicense scans, with
    two E8 callers each followed by the supplied compare/sete idiom.
    """
    data = bytearray(0x400)
    ret1 = 0x80
    data[ret1 : ret1 + len(SIG_RET_NOTIFY1)] = SIG_RET_NOTIFY1
    target = 0x180
    data[target : target + len(ISVAL_PROLOGUE)] = ISVAL_PROLOGUE
    for call_off in (0x120, 0x140):
        data[call_off : call_off + 5] = _e8(call_off, target)
        data[call_off + 5 : call_off + 5 + len(idiom)] = idiom
    ret2 = 0x300
    data[ret2 : ret2 + len(SIG_RET_NOTIFY2)] = SIG_RET_NOTIFY2
    return data, target


class TestCallerConvention:
    def test_cmp1_returns_1(self) -> None:
        data = bytearray(0x40)
        data[0:5] = _e8(0, 0x100)
        data[5 : 5 + len(CMP1_IDIOM)] = CMP1_IDIOM
        assert _caller_convention(_md(), bytes(data), 0) == 1

    def test_test_eax_returns_0(self) -> None:
        data = bytearray(0x40)
        data[0:5] = _e8(0, 0x100)
        data[5 : 5 + len(TEST_IDIOM)] = TEST_IDIOM
        assert _caller_convention(_md(), bytes(data), 0) == 0

    def test_cmp_magic_returns_immediate(self) -> None:
        data = bytearray(0x40)
        data[0:5] = _e8(0, 0x100)
        data[5 : 5 + len(CMP_MAGIC_IDIOM)] = CMP_MAGIC_IDIOM
        assert _caller_convention(_md(), bytes(data), 0) == 0x118

    def test_none_when_no_sete(self) -> None:
        data = bytearray(0x40)
        data[0:5] = _e8(0, 0x100)
        data[5:9] = b"\x90\x90\x90\x90"
        assert _caller_convention(_md(), bytes(data), 0) is None


class TestLocateIsValidLicense:
    def test_detects_ret1_convention(self) -> None:
        data, target = _build(CMP1_IDIOM)
        off, valid = _locate_isvalidlicense(_md(), bytes(data), 0x80, 0x300)
        assert off == target
        assert valid == 1

    def test_detects_ret0_convention(self) -> None:
        data, target = _build(TEST_IDIOM)
        off, valid = _locate_isvalidlicense(_md(), bytes(data), 0x80, 0x300)
        assert off == target
        assert valid == 0

    def test_detects_magic_value_convention(self) -> None:
        data, target = _build(CMP_MAGIC_IDIOM)
        off, valid = _locate_isvalidlicense(_md(), bytes(data), 0x80, 0x300)
        assert off == target
        assert valid == 0x118

    def test_raises_when_no_candidate(self) -> None:
        data = bytearray(0x400)
        data[0x80 : 0x80 + len(SIG_RET_NOTIFY1)] = SIG_RET_NOTIFY1
        data[0x300 : 0x300 + len(SIG_RET_NOTIFY2)] = SIG_RET_NOTIFY2
        with pytest.raises(SystemExit):
            _locate_isvalidlicense(_md(), bytes(data), 0x80, 0x300)
