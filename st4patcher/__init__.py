"""st4patcher - Sublime Text 4 (Linux x64) license-window RE tooling and patcher.

Owner-authorized, for plugin-development testing on the owner's own installed copy.

Public surface:
    constants  - patch sites (SITES), recipe md5s, hosts block, signatures, VA_BIAS
    patcher    - md5(), report(), apply_patches() (pure-logic, no capstone)
    locate     - signature-based offset locator (needs capstone)

Console entry point: `st4patch` (see st4patcher.__main__:main).
"""

from __future__ import annotations

from st4patcher import constants
from st4patcher.patcher import apply_patches, md5, report

__all__ = ["apply_patches", "constants", "md5", "report"]
