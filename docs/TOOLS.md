# Tools

Tooling used (or worth using) for the binary analysis in this repo. Feel free to
suggest more and install them, ideally via `mise` / `bunx` / `uvx` / `apt`.

## llvm

LLVM binutils, used ad-hoc for string extraction and disassembly cross-checks.
`llvm-strings-18 sublime_text > sublime_text.strings.txt` dumps every string
literal (used to locate the license `.rodata` markers in
`research/sublime-4205-license-patch.md`); `llvm-objdump -d` is an alternative
disassembler to GNU `objdump` below.

- https://llvm.org/docs/CommandGuide/llvm-strings.html
- https://llvm.org/docs/CommandGuide/llvm-objdump.html

## pyelftools

Pure-Python ELF/DWARF parser. This repo depends on it (`pyelftools>=0.31`) for
reading the Sublime Text ELF binary headers and sections.

- https://github.com/eliben/pyelftools
- https://github.com/eliben/pyelftools/raw/refs/tags/v0.33/doc/user-guide.md
- https://github.com/eliben/pyelftools/raw/refs/tags/v0.33/doc/hacking-guide.md

## objdump

GNU binutils disassembler. Produced the (very large) full disassembly dump under
`research/objdumps/`.

The verbatim `objdump --help` capture is omitted for brevity — see the GNU
binutils objdump docs: `man objdump`, or
<https://sourceware.org/binutils/docs/binutils/objdump.html>.

- https://github.com/CyberGrandChallenge/binutils/raw/refs/heads/master/binutils/objdump.h

## capstone

Disassembly framework used by `st4patcher/locate_sites.py` for the
version-resilient signature locator (`capstone>=5.0`).

- https://github.com/capstone-engine/capstone