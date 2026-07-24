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

- https://github.com/CyberGrandChallenge/binutils/raw/refs/heads/master/binutils/objdump.h

```
❯ objdump --help
Usage: objdump <option(s)> <file(s)>
 Display information from object <file(s)>.
 At least one of the following switches must be given:
  -a, --archive-headers    Display archive header information
  -f, --file-headers       Display the contents of the overall file header
  -p, --private-headers    Display object format specific file header contents
  -P, --private=OPT,OPT... Display object format specific contents
  -h, --[section-]headers  Display the contents of the section headers
  -x, --all-headers        Display the contents of all headers
  -d, --disassemble        Display assembler contents of executable sections
  -D, --disassemble-all    Display assembler contents of all sections
      --disassemble=<sym>  Display assembler contents from <sym>
  -S, --source             Intermix source code with disassembly
      --source-comment[=<txt>] Prefix lines of source code with <txt>
  -s, --full-contents      Display the full contents of all sections requested
  -Z, --decompress         Decompress section(s) before displaying their contents
  -g, --debugging          Display debug information in object file
  -e, --debugging-tags     Display debug information using ctags style
  -G, --stabs              Display (in raw form) any STABS info in the file
  -W, --dwarf[a/=abbrev, A/=addr, r/=aranges, c/=cu_index, L/=decodedline,
              f/=frames, F/=frames-interp, g/=gdb_index, i/=info, o/=loc,
              m/=macro, p/=pubnames, t/=pubtypes, R/=Ranges, l/=rawline,
              s/=str, O/=str-offsets, u/=trace_abbrev, T/=trace_aranges,
              U/=trace_info]
                           Display the contents of DWARF debug sections
  -Wk,--dwarf=links        Display the contents of sections that link to
                            separate debuginfo files
  -WK,--dwarf=follow-links
                           Follow links to separate debug info files (default)
  -WN,--dwarf=no-follow-links
                           Do not follow links to separate debug info files
  -L, --process-links      Display the contents of non-debug sections in
                           separate debuginfo files.  (Implies -WK)
      --ctf[=SECTION]      Display CTF info from SECTION, (default `.ctf')
      --sframe[=SECTION]   Display SFrame info from SECTION, (default '.sframe')
  -t, --syms               Display the contents of the symbol table(s)
  -T, --dynamic-syms       Display the contents of the dynamic symbol table
  -r, --reloc              Display the relocation entries in the file
  -R, --dynamic-reloc      Display the dynamic relocation entries in the file
  @<file>                  Read options from <file>
  -v, --version            Display this program's version number
  -i, --info               List object formats and architectures supported
  -H, --help               Display this information

 The following switches are optional:
  -b, --target=BFDNAME           Specify the target object format as BFDNAME
  -m, --architecture=MACHINE     Specify the target architecture as MACHINE
  -j, --section=NAME             Only display information for section NAME
  -M, --disassembler-options=OPT Pass text OPT on to the disassembler
  -EB --endian=big               Assume big endian format when disassembling
  -EL --endian=little            Assume little endian format when disassembling
      --file-start-context       Include context from start of file (with -S)
  -I, --include=DIR              Add DIR to search list for source files
  -l, --line-numbers             Include line numbers and filenames in output
  -F, --file-offsets             Include file offsets when displaying information
  -C, --demangle[=STYLE]         Decode mangled/processed symbol names
                                   STYLE can be "none", "auto", "gnu-v3",
                                   "java", "gnat", "dlang", "rust"
      --recurse-limit            Enable a limit on recursion whilst demangling
                                  (default)
      --no-recurse-limit         Disable a limit on recursion whilst demangling
  -w, --wide                     Format output for more than 80 columns
  -U[d|l|i|x|e|h]                Controls the display of UTF-8 unicode characters
  --unicode=[default|locale|invalid|hex|escape|highlight]
  -z, --disassemble-zeroes       Do not skip blocks of zeroes when disassembling
      --start-address=ADDR       Only process data whose address is >= ADDR
      --stop-address=ADDR        Only process data whose address is < ADDR
      --no-addresses             Do not print address alongside disassembly
      --prefix-addresses         Print complete address alongside disassembly
      --[no-]show-raw-insn       Display hex alongside symbolic disassembly
      --insn-width=WIDTH         Display WIDTH bytes on a single line for -d
      --adjust-vma=OFFSET        Add OFFSET to all displayed section addresses
      --show-all-symbols         When disassembling, display all symbols at a given address
      --special-syms             Include special symbols in symbol dumps
      --inlines                  Print all inlines for source line (with -l)
      --prefix=PREFIX            Add PREFIX to absolute paths for -S
      --prefix-strip=LEVEL       Strip initial directory names for -S
      --dwarf-depth=N            Do not display DIEs at depth N or greater
      --dwarf-start=N            Display DIEs starting at offset N
      --dwarf-check              Make additional dwarf consistency checks.
      --ctf-parent=NAME          Use CTF archive member NAME as the CTF parent
      --visualize-jumps          Visualize jumps by drawing ASCII art lines
      --visualize-jumps=color    Use colors in the ASCII art
      --visualize-jumps=extended-color
                                 Use extended 8-bit color codes
      --visualize-jumps=off      Disable jump visualization
      --disassembler-color=off       Disable disassembler color output. (default)
      --disassembler-color=terminal  Enable disassembler color output if displaying on a terminal.
      --disassembler-color=on        Enable disassembler color output.
      --disassembler-color=extended  Use 8-bit colors in disassembler output.

objdump: supported targets: elf64-x86-64 elf32-i386 elf32-iamcu elf32-x86-64 pei-i386 pe-x86-64 pei-x86-64 elf64-little elf64-big elf32-little elf32-big pe-bigobj-x86-64 pe-i386 pdb srec symbolsrec verilog tekhex binary ihex plugin
objdump: supported architectures: i386 i386:x86-64 i386:x64-32 i8086 i386:intel i386:x86-64:intel i386:x64-32:intel iamcu iamcu:intel

The following i386/x86-64 specific disassembler options are supported for use
with the -M switch (multiple options should be separated by commas):
  x86-64      Disassemble in 64bit mode
  i386        Disassemble in 32bit mode
  i8086       Disassemble in 16bit mode
  att         Display instruction in AT&T syntax
  intel       Display instruction in Intel syntax
  att-mnemonic  (AT&T syntax only)
              Display instruction with AT&T mnemonic
  intel-mnemonic  (AT&T syntax only)
              Display instruction with Intel mnemonic
  addr64      Assume 64bit address size
  addr32      Assume 32bit address size
  addr16      Assume 16bit address size
  data32      Assume 32bit data size
  data16      Assume 16bit data size
  suffix      Always display instruction suffix in AT&T syntax
  amd64       Display instruction in AMD64 ISA
  intel64     Display instruction in Intel64 ISA

Options supported for -P/--private switch:
For PE files:
  header      Display the file header
  sections    Display the section headers
Report bugs to <https://sourceware.org/bugzilla/>.

```

## capstone

Disassembly framework used by `st4patcher/locate_sites.py` for the
version-resilient signature locator (`capstone>=5.0`).

- https://github.com/capstone-engine/capstone
