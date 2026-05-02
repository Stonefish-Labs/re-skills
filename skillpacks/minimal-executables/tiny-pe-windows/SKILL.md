---
name: tiny-pe-windows
description: Specialized workflow for creating and minimizing Windows PE executables for PE32 i386 and PE32+ x86_64. Use this skill whenever a user asks for tiny Windows EXEs, PE headers, imports by name, MessageBox or ExitProcess stubs, section/file alignment, DOS/PE header overlap, import-table compression, 32-bit versus 64-bit PE caveats, or reproducing TinyPE-style binary golf on Windows loaders.
---

# Tiny PE Windows

Use this skill to build or explain tiny Windows PE files for PE32 `i386` and PE32+ `x86_64`.

## Workflow

1. Choose PE flavor:
   - **PE32 i386** for 32-bit Intel Windows executables.
   - **PE32+ x86_64** for 64-bit Windows executables.
2. Choose behavior. `ExitProcess`/return stubs are smallest; GUI APIs such as `MessageBoxW` prove imports and strings but cost bytes.
3. Start from a conservative baseline, then shrink by removing unused fields, merging sections, lowering alignment, and finally overlapping headers, data, import tables, and code when the target Windows loader accepts it.
4. Use `scripts/emit_tiny_pe.py` to emit known fixtures and baseline PE32/PE32+ templates. Keep TinyPE-style claims tied to the Windows version and import constraints used.
5. Validate with `file`, PE inspection tools, and native Windows execution when possible. Wine can smoke-test behavior but is not a substitute for Windows loader proof.

## References

- `references/pe-notes.md`: PE structure and TinyPE-style reduction sequence.
- `references/pe32-vs-pe64.md`: 32-bit and 64-bit header/import differences.

## Common Commands

```sh
python3 scripts/emit_tiny_pe.py --arch x86_64 --variant tinype-final --output tiny64.exe
python3 scripts/emit_tiny_pe.py --arch i386 --variant baseline --output tiny32.exe
```
