---
name: tiny-macho-macos
description: Specialized workflow for creating minimal macOS arm64 Mach-O executables and research artifacts. Use this skill whenever a user asks for tiny Mach-O binaries, Apple Silicon syscall stubs, LC_UNIXTHREAD, LC_MAIN, dyld requirements, ad hoc code signatures, __PAGEZERO/__TEXT layouts, otool/codesign validation, or why static arm64 executables are killed on release macOS. It intentionally scopes macOS support to arm64.
---

# Tiny Mach-O macOS

Use this skill for macOS `arm64` only. Do not imply Intel macOS support unless the user explicitly asks for a separate exploration.

## Workflow

1. Decide whether the user needs a runnable binary or a static research artifact.
   - Runnable release macOS arm64 binaries need dyld and an ad hoc signature.
   - Static syscall-only Mach-O files can be valid and signed, but release XNU rejects static `MH_EXECUTE` on arm64 before user code runs.
2. Use `scripts/make_tiny_macho.py` for signed static research artifacts and dynamic source templates.
3. Validate with `file`, `otool -hv -l`, `codesign --verify`, and native execution only for dynamic runnable artifacts.
4. Explain page-size and signing floors. On Apple Silicon, the meaningful payload can be small while the file is larger because of page alignment and embedded CodeDirectory data.

## References

- `references/macho-notes.md`: Mach-O load-command structure and arm64 entry options.
- `references/signing-and-loader-caveats.md`: ad hoc signatures, dyld, and static-exec rejection.

## Common Commands

```sh
python3 scripts/make_tiny_macho.py --output-dir out --emit all
```
