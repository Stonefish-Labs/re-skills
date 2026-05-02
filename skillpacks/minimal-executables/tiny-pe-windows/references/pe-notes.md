# Windows PE Notes

## Conservative Shape

- DOS header with `MZ` and `e_lfanew`.
- PE signature `PE\0\0`.
- COFF file header.
- PE32 or PE32+ optional header.
- At least one section for a normal linker-style baseline.

## TinyPE-Style Reduction

1. Compile a normal program.
2. Remove default libraries and merge sections.
3. Zero unused fields to reveal compression opportunities.
4. Rebuild as flat NASM bytes with computed offsets.
5. Lower file/section alignment where the target Windows loader allows it.
6. Overlap DOS header, PE header, optional header, imports, strings, and code.
7. Trim trailing zeros only when the loader supplies equivalent zero-fill behavior.

## Validation

Use Windows-native execution for final proof. PE parsers and Wine are useful but can disagree with Windows loader behavior.
