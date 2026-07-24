# Expected downloaded artifacts (indicator)

`download.sh` populates `<channel>/build-<N>/` with these 10 artifacts per build. The binaries themselves are git-ignored (large, re-downloadable); this file plus the `.gitkeep` markers preserve the directory shape in git.

| arch key  | filename (build 4XXX example)            |
|-----------|------------------------------------------|
| win       | `sublime_text_build_4XXX_x64_setup.exe`  |
| mac       | `sublime_text_build_4XXX_mac.zip`        |
| x64_linux | `sublime_text_build_4XXX_x64.zip`        |
| x64_tar   | `sublime_text_build_4XXX_x64.tar.xz`     |
| arm_tar   | `sublime_text_build_4XXX_arm64.tar.xz`   |
| amd_deb   | `sublime-text_build-4XXX_amd64.deb`      |
| arm_deb   | `sublime-text_build-4XXX_arm64.deb`      |
| rpm       | `sublime-text-4XXX-1.x86_64.rpm`         |
| pkg_x86   | `sublime-text-4XXX-1-x86_64.pkg.tar.xz`  |
| pkg_arm   | `sublime-text-4XXX-1-aarch64.pkg.tar.xz` |

Channels are assigned from the official APT `Packages` indices, cached in
`official-versions.json` (see the repo README "Build channels" section):

* `sublime-text-stable/` - build is in the official stable index (e.g. 4200),
* `sublime-text-dev/` - build is in the official dev index (e.g. 4199, 4205),
* `unlisted-dev-builds/` - build is in neither index (e.g. 4201-4204).

Regenerate any build: `./download.sh 4205`. Refresh the channel cache from the
live indices first with `./download.sh --refresh-channels 4205` (or
`mise run channels:refresh`).
