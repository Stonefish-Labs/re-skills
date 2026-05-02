---
name: tiny-elf-linux
description: Specialized workflow for creating and minimizing Linux ELF executables for x86_64 and i386. Use this skill whenever a user asks for tiny Linux binaries, ELF header construction, syscall-only exit/write programs, static no-libc files, ELF32 versus ELF64 choices, program-header overlap, readelf/file validation, or native Linux loader proof. It covers conservative spec-readable builds and aggressive loader-oriented binary-golf variants.
---

# Tiny ELF Linux

Use this skill to build or explain minimal Linux ELF binaries for `x86_64` and `i386`.

## Workflow

1. Choose architecture: `x86_64` for modern 64-bit Linux, `i386` for 32-bit Intel Linux. Read `references/syscall-abi.md` when syscall register conventions matter.
2. Choose tier:
   - **Conservative**: standard ELF header + one program header + code. Prefer this for teaching and parser compatibility.
   - **Aggressive**: overlap ELF/program-header fields when the user wants the smallest loader-oriented artifact.
3. Generate bytes with `scripts/make_tiny_elf.py` instead of hand-typing headers. The script supports `exit` and `write` behaviors for both architectures.
4. Validate with `file`, `readelf -h -l` when available, `wc -c`, and native execution on Linux with the matching architecture.
5. State whether execution was native, emulated, or skipped. QEMU/Docker on another host is useful but is not the same as native Linux loader proof.

## References

- `references/elf-notes.md`: ELF32/ELF64 fields and safe overlap ideas.
- `references/syscall-abi.md`: syscall numbers and calling conventions.
- `references/loader-caveats.md`: Linux loader behavior, parser warnings, and verification limits.

## Common Commands

```sh
python3 scripts/make_tiny_elf.py --arch x86_64 --behavior exit --tier aggressive --output tiny_exit
python3 scripts/make_tiny_elf.py --arch i386 --behavior write --tier conservative --output tiny_write32
```
