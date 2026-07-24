# Disclaimer

Read this before using anything in this repository.

## What this project is

`sublime-text-4-dev-patcher` is a **reverse-engineering record** and a
**patcher** for the startup license window of Sublime Text 4 (Linux x64). It
exists so that developers can test their own software (for example, plugins for
the new Python 3.14 plugin host) against `dev` builds, and so that security and
interoperability researchers can study how the startup license check works on a
copy of Sublime Text they already own.

## What this project is not

- It is **not** affiliated with, authorized by, or endorsed by Sublime HQ Pty
  Ltd, the makers of Sublime Text.
- It ships **no Sublime Text binaries**, **no extracted Sublime Text assets**,
  and **no license keys**. You bring your own lawfully obtained copy.
- It is **not** a way to avoid paying for software. If you use Sublime Text,
  [buy a license](https://www.sublimehq.com/store/text) and follow its terms.

## Intended use

Use this material only:

- to develop and test your own software against builds you are entitled to run;
  or
- for interoperability, security, and reverse-engineering research on a copy of
  Sublime Text you already lawfully own and installed.

Patch a **user-owned copy** of the binary. Do not distribute a patched binary.

## Legal note

Modifying software to change how a license or activation check behaves may be
restricted in your jurisdiction. Depending on where you are, anti-circumvention
laws (for example, the U.S. DMCA §1201, the EU Information Society Directive
2001/29/EC Article 6, and the EU Software Directive 2009/24/EC) may apply.
Reverse engineering for interoperability and security research is permitted in
some jurisdictions and under some conditions, and prohibited in others. Nothing
here is legal advice.

**You are solely responsible for ensuring your use of this project is lawful
where you are.** If in doubt, consult a qualified lawyer, and do not use the
patcher on a copy you do not own.

## No warranty

The material is provided "as is", without warranty of any kind. See
[`LICENSE`](LICENSE) for the full terms.
