# Validation Matrix

Tiny executable work needs precise evidence labels.

| Claim | Evidence | Notes |
| --- | --- | --- |
| Tool-readable | `file`, `readelf`, `otool`, PE parsers | Does not prove OS loader execution |
| Loader-accepted | Target OS maps and starts the image | May still crash if entry code is wrong |
| Native-proven | Runs on target OS and CPU | Strongest proof |
| Emulator-runnable | QEMU/Wine/Docker smoke test | Useful, but label as emulated |
| Hex-stable | binary-to-hex-to-binary comparison | Proves artifact reproducibility |

## Verification Rules

- Record exact OS and architecture for native runs.
- Treat parser warnings as data, not automatic failure; aggressive artifacts often trade parser cleanliness for size.
- Check absence of accidental dynamic dependencies when a syscall-only artifact is intended.
- For macOS arm64, `codesign --verify` can pass even though release XNU rejects static non-dyld `MH_EXECUTE`.
