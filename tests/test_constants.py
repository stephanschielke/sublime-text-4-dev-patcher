import pytest

from st4patcher.constants import HOSTS_NEW, HOSTS_OLD, SITE_TO_LOCATE_KEY, SITES, isval_payload


def test_sites_old_and_new_lengths_match() -> None:
    for name, _off, old, new in SITES:
        assert len(old) == len(new), name


def test_site_to_locate_key_covers_site_names_exactly() -> None:
    assert set(SITE_TO_LOCATE_KEY) == {name for name, _off, _old, _new in SITES}


def test_hosts_lengths_match() -> None:
    assert len(HOSTS_NEW) == len(HOSTS_OLD)


class TestIsvalPayload:
    def test_ret1_default_slot(self) -> None:
        out = isval_payload(1)
        assert out == bytes.fromhex("4831c048ffc0c390")  # xor rax,rax; inc rax; ret; nop
        assert len(out) == 8

    def test_ret0_default_slot(self) -> None:
        out = isval_payload(0)
        assert out == bytes.fromhex("4831c0c390909090")  # xor rax,rax; ret; nop*4
        assert len(out) == 8

    def test_custom_slot_widens_with_nops(self) -> None:
        out = isval_payload(1, slot=10)
        assert out == bytes.fromhex("4831c048ffc0c3") + b"\x90" * 3
        assert len(out) == 10

    def test_magic_value_uses_mov_eax_imm32(self) -> None:
        out = isval_payload(0x118)  # 4201 convention: callers do cmp eax,0x118
        assert out == bytes.fromhex("b818010000c39090")  # mov eax,0x118; ret; nop*2
        assert len(out) == 8

    def test_magic_value_two_keeps_mov_not_xor(self) -> None:
        out = isval_payload(2)
        assert out == bytes.fromhex("b802000000c39090")  # mov eax,2; ret; nop*2
        assert len(out) == 8

    @pytest.mark.parametrize("bad", [-1, 0x1_0000_0000])
    def test_out_of_uint32_raises(self, bad: int) -> None:
        with pytest.raises(ValueError, match="uint32"):
            isval_payload(bad)

    def test_slot_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="too small"):
            isval_payload(1, slot=3)
