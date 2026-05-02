# re-skills

Portable agent skills for reverse engineering, binary formats, executable
minimalism, and related security research workflows.

This repository is organized as skill packs so related skills can be copied,
installed, reviewed, and versioned together without turning the repo root into a
flat pile of unrelated capabilities.

## Skill Packs

- [`skillpacks/minimal-executables`](skillpacks/minimal-executables/): build,
  shrink, and verify tiny executable files across Linux ELF, macOS Mach-O, and
  Windows PE.

Future packs can live beside it, for example:

- `skillpacks/reverse-engineering/`
- `skillpacks/offensive-security/`
- `skillpacks/binary-analysis/`

## Layout

Each pack may contain multiple plain skill folders. A skill folder is portable:
it has a `SKILL.md` plus optional `references/`, `assets/`, `scripts/`, and
`agents/` directories. This avoids requiring a Codex plugin wrapper while still
working well in Claude Code, Cursor, Codex, opencode, Pi Agent, and similar
agent runtimes.

Use the pack README first when a pack has one. It explains which skill is the
entrypoint and which specialist skills should be kept together.

## Minimal Executables Smoke Test

```sh
cd skillpacks/minimal-executables
python3 minimal-executable-builder/scripts/measure_binary.py --json /bin/ls
python3 tiny-elf-linux/scripts/make_tiny_elf.py --arch x86_64 --behavior exit --tier aggressive --output /tmp/tiny_exit
python3 tiny-macho-macos/scripts/make_tiny_macho.py --output-dir /tmp/tiny_macho --emit static
python3 tiny-pe-windows/scripts/emit_tiny_pe.py --arch x86_64 --variant tinype-final --output /tmp/tiny.exe
```
