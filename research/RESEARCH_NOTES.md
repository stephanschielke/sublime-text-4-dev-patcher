# Prior-Art Patch Catalog

A high-level summary of publicly published Sublime Text / Sublime Merge license patches, collected as reference material for this project.

> For full source URLs and the consolidated version/OS/patch mapping, see
> [`sources-and-version-map.md`](sources-and-version-map.md).

## Platform x version overview

| Platform | Version | Source ID | Strategy |
|---|---|---|---|
| Windows x64 | ST3 3211 | SRC-GIST-WAL | offset edit |
| Linux/macOS/Windows | ST4 a4094 | SRC-GIST-WAL | flag-store force |
| Windows x64 | ST4 a4098 | SRC-GIST-WAL | flag-store force |
| Windows x64 | ST4 4000-4199 | SRC-RUST-4000 | flag-store force |
| Windows x64 | ST4 4107 | SRC-GIST-JERRY | RSA-fn + host |
| (tutorial) | ST4 4121 | SRC-GIST-OPA | concepts only |
| macOS | ST4 4126 | SRC-GIST-DEST | flag-store force |
| Windows x64 | ST4 4200 | SRC-RUST-4200, SRC-GIST-FADI | flag-store force |
| macOS x86_64 | ST4 4200 | SRC-REPO-QZ, SRC-GIST-MAC-4200 | 5-site |
| macOS ARM64 | ST4 4200 | SRC-GIST-MAC-4200 | 5-site |
| **Linux x64** | **ST4 4200** | **SRC-GIST-LINUX-4200** | **5-site (basis for this project)** |
| **Linux x64** | **ST4 4205** | **this project** | **EXP-RET1 to PATCH-4205-A** |
| **Linux x64** | **ST4 4206-4207** | **this project** | **280-convention (PATCH-4206-A / PATCH-4207-A)** |
| Windows x64 | ST4 4107-4206 | SRC-PATCHER | signature scan |
| Linux x64 | Sublime Merge 2112/2121 | SRC-GIST-MAC-4200, SRC-GIST-JERRY | not Sublime Text |

The 5-site Linux recipe from SRC-GIST-LINUX-4200 is the foundation this project ports forward.
See [`sources-and-version-map.md`](sources-and-version-map.md) for real URLs and full mapping.
