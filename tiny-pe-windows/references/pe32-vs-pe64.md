# PE32 vs PE32+

| Topic | PE32 i386 | PE32+ x86_64 |
| --- | --- | --- |
| COFF machine | `0x14c` | `0x8664` |
| Optional magic | `0x10b` | `0x20b` |
| ImageBase size | 32-bit | 64-bit |
| BaseOfData | Present | Removed |
| Calling convention | stack-based stdcall/cdecl patterns | Windows x64 register convention |
| Imports | IMAGE_IMPORT_DESCRIPTOR and thunks | Same concept, wider pointers |

For import-heavy tiny binaries, PE32 can win because instructions and pointers are smaller. PE32+ can still be very small when exploiting relaxed loader behavior and careful header overlap, as in the TinyPE-on-Win10 final x64 artifact.
