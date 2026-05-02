---
name: minimal-executable-builder
description: Portable workflow for designing, generating, shrinking, and verifying minimal executable binaries across Linux ELF, Windows PE, and macOS Mach-O. Use this skill whenever a user asks for tiny binaries, smallest executable files, handcrafted ELF/PE/Mach-O layouts, syscall-only programs, header overlap, binary golf, loader-caveat analysis, or cross-platform executable minimization, even if they only mention one platform. It coordinates specialist format skills and keeps tool-readable, loader-accepted, and native-proven claims separate.
---

# Minimal Executable Builder

Use this skill as the coordinator when a task spans formats, architectures, or verification tiers.

## Workflow

1. Identify target OS, format, architecture, behavior, and proof level. Read `references/decision-tree.md` when the user has not already made those choices.
2. Route format-specific work to the specialist skill:
   - Linux ELF `x86_64` or `i386`: use `tiny-elf-linux`.
   - Windows PE32 `i386` or PE32+ `x86_64`: use `tiny-pe-windows`.
   - macOS Mach-O `arm64`: use `tiny-macho-macos`.
3. Keep three claims separate because confusing them produces false confidence:
   - **Tool-readable**: parsers such as `file`, `readelf`, `otool`, or PE tools accept the file.
   - **Loader-accepted**: the OS loader can map it, even if tools warn.
   - **Native-proven**: the artifact was executed on the real target OS/architecture.
4. Prefer deterministic scripts for byte emission. Use `scripts/measure_binary.py` and `scripts/hex_roundtrip.py` to measure, serialize, and check artifacts before explaining results.
5. Explain caveats in output. Tiny executables often exploit loader behavior that is version-, architecture-, or policy-specific.

## Skill-Scoped Agents

Read these agent files when a task is complex enough to benefit from an independent pass:

- `agents/format-scout.md`: choose target format, architecture, and validation tier.
- `agents/size-golfer.md`: look for size reductions while preserving loader invariants.
- `agents/loader-verifier.md`: design verification and label evidence honestly.

## References

- `references/decision-tree.md`: choose platform, architecture, tier, and specialist skill.
- `references/validation-matrix.md`: map proof claims to commands and caveats.
- `references/tool-portability.md`: write instructions that travel across Claude Code, Cursor, Codex, opencode, and Pi Agent.

## Output Pattern

Report the final artifact with: target, architecture, behavior, byte size, generation path, validation commands run, and any caveat that prevents stronger claims.
