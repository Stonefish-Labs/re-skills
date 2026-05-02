# re-skills: Minimal Executable Skill Suite

Portable agent skills for building, shrinking, and verifying tiny executable files.

## Skills

- `minimal-executable-builder`: cross-platform router and verification discipline.
- `tiny-elf-linux`: Linux ELF for `x86_64` and `i386`.
- `tiny-macho-macos`: macOS `arm64` Mach-O, including release macOS caveats.
- `tiny-pe-windows`: Windows PE32 `i386` and PE32+ `x86_64`.

The individual skill folders intentionally do not contain README files. This package README is the distribution-level inventory for Claude Code, Cursor, Codex, opencode, Pi Agent, and similar agent runtimes.

## Smoke Test

```sh
python3 minimal-executable-builder/scripts/measure_binary.py --json /bin/ls
python3 tiny-elf-linux/scripts/make_tiny_elf.py --arch x86_64 --behavior exit --tier aggressive --output /tmp/tiny_exit
python3 tiny-macho-macos/scripts/make_tiny_macho.py --output-dir /tmp/tiny_macho --emit static
python3 tiny-pe-windows/scripts/emit_tiny_pe.py --arch x86_64 --variant tinype-final --output /tmp/tiny.exe
```
