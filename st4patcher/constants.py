"""Patch data and recipes for the Sublime Text 4 (Linux x64 ELF) license window.

Two layers live here:

* **Build-invariant signatures + payload builders** -- used by the generic,
  version-agnostic locator (:mod:`st4patcher.locate_sites`) and patcher
  (:mod:`st4patcher.patcher`). These work on ANY Linux x64 build whose license
  gate is reachable by the documented idioms, not just 4205.
* **The 4205 reference fixture** (``SITES``, ``CLEAN_MD5``, ``RECIPE_MD5``,
  ``SIG_ISVALID_CALLER``) -- the hand-verified ground truth for build 4205,
  kept for the ``--locate`` cross-check and regression tests. It is NOT the
  primary patch path anymore.

The IsValidLicense convention boundary: builds < 4205 expect IsValidLicense to
return 0 ("valid"), with callers doing ``test eax,eax``; builds >= 4205 expect 1,
with callers doing ``cmp eax,1``. The patcher infers which from the caller idiom
and emits the matching return payload, so it no longer hardcodes "return 1".

See research/sublime-4205-license-patch.md and
research/cross-build-generalization.md for the full RE record.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
#  4205 reference fixture: known md5s (size-preserving recipes)
# --------------------------------------------------------------------------- #
CLEAN_MD5 = "c7539dda818f0c3537ba6cfa0f872fa9"  # pristine 4205 source binary

# Verified recipe outputs (md5 of the patched binary).
RECIPE_MD5 = {
    "PATCH-4205-A": "4eec4c3506773e9899cdbe8e463ab9c0",  # S1..S5      (CONFIRMED WORKING)
    "PATCH-4205-A-hosts": "b2ad2138435a548bbe7093a5807bba30",  # S1..S5 + hosts
    "PATCH-4205-B": "d36770200e4c710854b969dc77baff3e",  # S4 only
}

# Clean-input md5s for builds the patcher has been validated against (advisory
# only; patching never requires a match -- the locator works by structure).
KNOWN_CLEAN_MD5 = {
    "4c62e941aeb0026cc5037541ed05cf0a": 4207,
    "edd8e1c2e77d7b4cb3fdeae692965b0a": 4206,
    "c7539dda818f0c3537ba6cfa0f872fa9": 4205,
    "2b330244b229185fe593de61e7713f4a": 4204,
    "04ceb353faa23db3bf452988e61c0cfe": 4203,
    "20470c89374eda4df1d8307c6e5b11c2": 4202,
    "ef601b774d0f845e5fb924b7f7d0cbda": 4201,
    "2de36b6755ac192ba0970bebcecf6c40": 4200,
    "e9b5fcaba01db4d7ddca7b61b0816fc1": 4199,
    "252afd2ebadc9042cd8464b4f2f8ca92": 4198,
    "1d3b475ea52de10d73bdb9c7a20d2078": 4197,
    "80d2d34f2883fd56e56b91680b508bdc": 4196,
    "1222bdd6496bde4cb598e0893c6646ae": 4195,
    "6a6451509a82a582aec7ba1ad357c053": 4194,
    "aca2045fab66dd71f316e1355a92b222": 4193,
    "e7665caec44a621081fd94eec41659b0": 4192,
    "2ed03924f45cf1ddc2a5aecb564b3d77": 4191,
    "86bdb8f699aa51776eb4c514d3bed55f": 4190,
    "8fe19770a6e30f6e3945ea022773e7c0": 4189,
    "9b2aa9a3189fd8b287c88cbb1b988d51": 4188,
    "c0863c48eda70997499d909e5dcac0d5": 4187,
    "9c60629fd51a7242b5174698b3e99ca2": 4186,
    "8f786da46314b8d49ad3d52c6dec4da7": 4185,
    "8a345430a309bd085637643da7524e1b": 4184,
    "ef3092f808f5bfe4033bca271930c581": 4183,
    "39641d45df53ed7d2dddf3547f41d233": 4182,
    "6b4922ab5d61cf2703810fb817cbf897": 4181,
    "386cc1fee9c957ddb9e93d93357ec5c7": 4180,
    "be5efe9cd716a74886521e87fdb45355": 4178,
    "d3cc733db6fb48726a05347a65227a87": 4177,
    "3f7f7d615c50796175ffe40b357fa881": 4176,
}

# --------------------------------------------------------------------------- #
#  4205 reference patch sites (fileoff; .text VA = fileoff + VA_BIAS)
#  (name, fileoff, original_bytes, replacement_bytes) -- same length each.
#  Used only by --locate cross-check and regression tests; the live patch path
#  uses offsets resolved at runtime by st4patcher.locate_sites.
# --------------------------------------------------------------------------- #
VA_BIAS = 0x1000  # .text VA = fileoff + 0x1000 on these builds.

SITES: list[tuple[str, int, bytes, bytes]] = [
    ("nop1_revalidate_cb", 0x53B097, bytes.fromhex("e814900e00"), bytes.fromhex("90" * 5)),
    ("nop2_revalidate_cb", 0x53B0B0, bytes.fromhex("e8fb8f0e00"), bytes.fromhex("90" * 5)),
    ("ret_notify1", 0x54D288, bytes.fromhex("41"), bytes.fromhex("c3")),
    # IsValidLicense -> return 1 (xor rax,rax; inc rax; ret; nop)
    ("isvalidlicense_ret1", 0x54D568, bytes.fromhex("5541574156415541"), bytes.fromhex("4831c048ffc0c390")),
    ("ret_notify2", 0x54EF4C, bytes.fromhex("41"), bytes.fromhex("c3")),
]

# Maps a SITES name to the key the signature locator returns.
SITE_TO_LOCATE_KEY = {
    "nop1_revalidate_cb": "nop1",
    "nop2_revalidate_cb": "nop2",
    "ret_notify1": "ret_notify1",
    "isvalidlicense_ret1": "isvalidlicense",
    "ret_notify2": "ret_notify2",
}

# --------------------------------------------------------------------------- #
#  Optional (--hosts) in-binary phone-home block
# --------------------------------------------------------------------------- #
HOSTS_OFF = 0xCF39C
HOSTS_OLD = b"license.sublimehq.com"
HOSTS_NEW = b"127.0.0.1" + b"\x00" * (len(HOSTS_OLD) - len("127.0.0.1"))

# --------------------------------------------------------------------------- #
#  Byte signatures used by the version-resilient locator
# --------------------------------------------------------------------------- #
SIG_ISVALID_CALLER = bytes.fromhex("83f8010f944705")  # cmp eax,1 ; sete [rdi+5]
SIG_RET_NOTIFY1 = bytes.fromhex("415741564154534881ec0803")
SIG_RET_NOTIFY2 = bytes.fromhex("415741565389f34989fe6a20")
SIG_NOP_CONST = bytes.fromhex("ba88130000e8")  # mov edx,0x1388 ; call

# --------------------------------------------------------------------------- #
#  Network redirection (--no-update, --no-crash)
# --------------------------------------------------------------------------- #
# A host string redirected to loopback: 127.0.0.1, NUL-padded to the original
# length so the connection never reaches the real server (stops the phone-home,
# not just the popup).
LOOPBACK = b"127.0.0.1"


def loopback_for(host: bytes) -> bytes:
    """127.0.0.1 NUL-padded to len(host); raises if host is shorter than that."""
    if len(host) < len(LOOPBACK):
        raise ValueError(f"host {host!r} shorter than {LOOPBACK!r}")
    return LOOPBACK + b"\x00" * (len(host) - len(LOOPBACK))


# Auto-updater. The updater resolves a dedicated host copy then GETs a
# channel-specific path. Both are redirected: the host to loopback (no request
# leaves the machine) and the path to a 404 route (defense-in-depth).
# The update host copy is the unique one flanked by the updater's own labels,
# distinct from the shared Buy/reissue copies of the same domain.
UPDATE_HOST = b"www.sublimetext.com"
UPDATE_HOST_ANCHOR = b"latest_version\x00" + UPDATE_HOST + b"\x00"
UPDATE_PATH_PREFIX = b"/updates/"
UPDATE_PATH_MARK = b"_update_check?version"  # unique; dev_ or stable_ per channel
UPDATE_PATH_KILL = b"/dev/null"  # same length as /updates/

# Crash reporter. The bundled crash_handler uploads minidumps to this host;
# redirecting it to loopback stops the upload. Unique in the main binary.
CRASH_HOST = b"crash-server.sublimehq.com"

# --------------------------------------------------------------------------- #
#  Build-agnostic patch payloads
# --------------------------------------------------------------------------- #
NOP_CALL = bytes.fromhex("90" * 5)  # replaces a 5-byte `call rel32`
RET = bytes.fromhex("c3")  # replaces the first prologue byte of a notify fn

ISVAL_RET1_CORE = bytes.fromhex("4831c048ffc0c3")  # xor rax,rax; inc rax; ret
ISVAL_RET0_CORE = bytes.fromhex("4831c0c3")  # xor rax,rax; ret

ISVAL_SLOT = 8  # bytes overwritten at IsValidLicense (matches proven 4205 recipe)


def isval_payload(valid_value: int, slot: int = ISVAL_SLOT) -> bytes:
    """Size-preserving IsValidLicense override that returns ``valid_value``.

    ``valid_value`` is the integer the build's callers treat as "valid": 0 (most
    builds, callers ``test eax,eax``), 1 (builds with ``cmp eax,1`` such as 4202
    and 4205), or an arbitrary status code (e.g. 0x118 on 4201, whose callers do
    ``cmp eax,0x118``). The 0 and 1 cases keep their proven minimal xor cores; any
    other value uses ``mov eax,imm32; ret`` (``b8 <imm32> c3``). All cores fit the
    fixed 8-byte slot and are NOP-right-padded, matching the hand-verified recipe.
    """
    if valid_value < 0 or valid_value > 0xFFFFFFFF:
        raise ValueError(f"valid_value must fit in uint32, got {valid_value}")
    if valid_value == 1:
        core = ISVAL_RET1_CORE
    elif valid_value == 0:
        core = ISVAL_RET0_CORE
    else:
        core = b"\xb8" + valid_value.to_bytes(4, "little") + b"\xc3"
    if len(core) > slot:
        raise ValueError(f"slot {slot} too small for payload {len(core)}")
    return core + b"\x90" * (slot - len(core))
