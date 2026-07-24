# Notice

## Trademarks and affiliation

"Sublime Text" and "Sublime Merge" are products and trademarks of
**Sublime HQ Pty Ltd**. This project is an independent, community
reverse-engineering effort. It is **not affiliated with, authorized by,
sponsored by, or endorsed by Sublime HQ Pty Ltd**. All trademarks are the
property of their respective owners and are used here only to identify the
software being studied.

## No bundled proprietary material

This repository contains **no Sublime Text binaries, no extracted Sublime Text
assets, and no license keys**. The binary under test is git-ignored and must be
obtained lawfully by the user from the official source
(<https://www.sublimetext.com/>). The reverse-engineering documents contain only
small addresses, byte facts, and disassembly excerpts required to explain how
the startup license check works, produced from a copy the operator already owns.

## Third-party dependencies

The patcher depends on the following open-source Python packages, declared in
`pyproject.toml` and not vendored into this repository:

- `capstone` — disassembly framework (BSD-3-Clause)
- `pyelftools` — ELF/DWARF parser (public domain / Unlicense)
- `debian-inspector` — Debian package index parsing (Apache-2.0)

## Prior art

Prior-art patch recipes referenced by this project are cited by their real
source URLs in [`research/sources-and-version-map.md`](research/sources-and-version-map.md).
Credit belongs to those original authors; see that file for attribution.

## Use

See [`LICENSE`](LICENSE) for the terms of use and [`DISCLAIMER.md`](DISCLAIMER.md)
for the legal disclaimer. If you use Sublime Text,
[buy a license](https://www.sublimehq.com/store/text).
