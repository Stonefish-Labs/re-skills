# Linux Syscall ABI

## x86_64

| Purpose | Register |
| --- | --- |
| syscall number | `rax` |
| arg1 | `rdi` |
| arg2 | `rsi` |
| arg3 | `rdx` |
| trap | `syscall` |

Common numbers: `write = 1`, `exit = 60`.

## i386

| Purpose | Register |
| --- | --- |
| syscall number | `eax` |
| arg1 | `ebx` |
| arg2 | `ecx` |
| arg3 | `edx` |
| trap | `int 0x80` |

Common numbers: `exit = 1`, `write = 4`.

## Byte-Golf Notes

Small constants can use `push imm8; pop reg` on x86_64. On i386, `xor eax,eax; inc eax` is compact for syscall `1`, but remember byte `0x40` is a REX prefix in long mode, not `inc eax`.
