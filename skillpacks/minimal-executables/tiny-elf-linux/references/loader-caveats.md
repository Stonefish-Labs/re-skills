# Linux ELF Loader Caveats

- Native execution on Linux with the matching CPU is the only native-proven result.
- `readelf` may reject or warn on intentionally overlapped artifacts that Linux still executes.
- Docker `--platform linux/amd64` on Apple Silicon is emulated; label it as a smoke test.
- `PT_INTERP` means the binary is dynamically linked; syscall-only minimal artifacts should not include it.
- Some kernel hardening settings may affect unusual low-address or nonstandard layouts.
