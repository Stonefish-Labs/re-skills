# Minimal Executable Decision Tree

Use this reference when the target is not already fully specified.

## Choose Format

| User target | Format | Specialist skill |
| --- | --- | --- |
| Linux, Unix-like Linux syscall binary | ELF | `tiny-elf-linux` |
| Windows `.exe`, PE, Win32, Win64 | PE | `tiny-pe-windows` |
| macOS, Apple Silicon | Mach-O arm64 | `tiny-macho-macos` |

## Choose Architecture

| Platform | Supported architectures |
| --- | --- |
| Linux ELF | `x86_64`, `i386` |
| Windows PE | PE32 `i386`, PE32+ `x86_64` |
| macOS Mach-O | `arm64` only |

## Choose Tier

| Tier | Use when | Typical caveat |
| --- | --- | --- |
| Conservative | Teaching, parser compatibility, safer starting point | Larger file |
| Aggressive | Binary golf, loader behavior research | Parsers may warn |
| Runnable modern | The user needs execution on today’s platform policies | May need dyld/signatures |

## Choose Behavior

Start with `exit(0)` to prove loader and entry. Move to `write(1, "hi\n", 3)` to prove syscalls/output. Use API imports only when the point is import-table behavior, such as Windows `MessageBoxW`.
