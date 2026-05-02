# Mach-O arm64 Notes

## Minimal Static Research Shape

- `mach_header_64`
- `LC_SEGMENT_64 __PAGEZERO`
- `LC_SEGMENT_64 __TEXT`
- `LC_UNIXTHREAD` with `ARM_THREAD_STATE64`
- `LC_SEGMENT_64 __LINKEDIT`
- `LC_CODE_SIGNATURE`

`__PAGEZERO` must cover the lower 4 GiB for arm64. `__TEXT` commonly starts at `0x100000000`.

## Runnable Release macOS Shape

Modern runnable arm64 command-line binaries normally use dyld:

- `LC_LOAD_DYLINKER`
- `LC_MAIN`
- `LC_LOAD_DYLIB /usr/lib/libSystem.B.dylib`
- `LC_CODE_SIGNATURE`

The dynamic binary can still have tiny user code; the loader policy floor dominates the file size.
