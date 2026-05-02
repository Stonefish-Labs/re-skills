# Minimal Executables Skill Pack

Portable agent skills for designing, generating, shrinking, and verifying tiny
executables across Linux ELF, macOS Mach-O, and Windows PE.

Use these skills together:

- `minimal-executable-builder`: entrypoint and cross-format router.
- `tiny-elf-linux`: Linux ELF specialist for `x86_64` and `i386`.
- `tiny-macho-macos`: macOS `arm64` Mach-O specialist.
- `tiny-pe-windows`: Windows PE32 `i386` and PE32+ `x86_64` specialist.

The builder skill chooses the target OS, executable format, architecture,
reduction tier, and verification strategy. The specialist skills hold the
format-specific ABI notes, loader caveats, generators, fixtures, and templates.

## Install Shape

For best results, install or copy all four skill folders together. If an agent
runtime only supports one skill at a time, start with
`minimal-executable-builder`, then bring in the matching specialist skill for the
target format:

- Linux tasks need `tiny-elf-linux`.
- macOS tasks need `tiny-macho-macos`.
- Windows tasks need `tiny-pe-windows`.

The pack is intentionally not wrapped as a Codex-only plugin. Plain skill
folders keep the material portable across Claude Code, Cursor, Codex, opencode,
Pi Agent, and other agents that can read local Markdown skills and companion
files.

## Smoke Test

Run from this directory:

```sh
python3 minimal-executable-builder/scripts/measure_binary.py --json /bin/ls
python3 tiny-elf-linux/scripts/make_tiny_elf.py --arch i386 --behavior exit --tier aggressive --output /tmp/tiny_exit_i386
python3 tiny-elf-linux/scripts/make_tiny_elf.py --arch x86_64 --behavior exit --tier aggressive --output /tmp/tiny_exit_x64
python3 tiny-macho-macos/scripts/make_tiny_macho.py --output-dir /tmp/tiny_macho --emit static
python3 tiny-pe-windows/scripts/emit_tiny_pe.py --arch x86_64 --variant tinype-final --output /tmp/tiny.exe
```

Native execution proof still belongs on the target platform. Parser output,
emulator runs, and native loader acceptance are separate evidence tiers.
