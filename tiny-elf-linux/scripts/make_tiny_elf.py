#!/usr/bin/env python3
import argparse
import os
import pathlib
import stat
import struct

MSG = b"hi\n"


def p16(n):
    return struct.pack("<H", n)


def p32(n):
    return struct.pack("<I", n)


def p64(n):
    return struct.pack("<Q", n)


def ident(bits):
    return b"\x7fELF" + bytes([2 if bits == 64 else 1, 1, 1, 0, 0]) + bytes(7)


def x64_exit():
    return bytes.fromhex("31ff6a3c580f05")


def x64_write(code_vaddr):
    code = bytearray()
    code += bytes.fromhex("6a0158")
    code += bytes.fromhex("6a015f")
    lea_at = len(code)
    code += b"\x48\x8d\x35" + b"\0\0\0\0"
    code += bytes([0x6A, len(MSG), 0x5A])
    code += bytes.fromhex("0f05")
    code += bytes.fromhex("31ff")
    code += bytes.fromhex("6a3c58")
    code += bytes.fromhex("0f05")
    msg_off = len(code)
    next_rip = code_vaddr + lea_at + 7
    code[lea_at + 3 : lea_at + 7] = struct.pack("<i", code_vaddr + msg_off - next_rip)
    code += MSG
    return bytes(code)


def i386_exit():
    return bytes.fromhex("31c04031dbcd80")


def i386_write(code_vaddr):
    code = bytearray()
    code += bytes.fromhex("31c0b004")
    code += bytes.fromhex("31db43")
    mov_at = len(code)
    code += b"\xb9\0\0\0\0"
    code += bytes([0xB2, len(MSG)])
    code += bytes.fromhex("cd80")
    code += i386_exit()
    msg_off = len(code)
    code[mov_at + 1 : mov_at + 5] = p32(code_vaddr + msg_off)
    code += MSG
    return bytes(code)


def elf64(code, tier):
    base = 0x400000
    if tier == "conservative":
        phoff, code_off = 64, 120
        size = code_off + len(code)
        out = bytearray()
        out += ident(64)
        out += p16(2) + p16(0x3E) + p32(1) + p64(base + code_off)
        out += p64(phoff) + p64(0) + p32(0) + p16(64) + p16(56) + p16(1)
        out += p16(0) + p16(0) + p16(0)
        out += p32(1) + p32(5) + p64(0) + p64(base) + p64(base)
        out += p64(size) + p64(size) + p64(0x1000)
        out += code
        return bytes(out), code_off

    phoff, code_off = 0x38, 0x68
    size = code_off + len(code)
    out = bytearray(size)
    out[0:16] = ident(64)
    out[0x10:0x12] = p16(2)
    out[0x12:0x14] = p16(0x3E)
    out[0x14:0x18] = p32(1)
    out[0x18:0x20] = p64(base + code_off)
    out[0x20:0x28] = p64(phoff)
    out[0x34:0x36] = p16(64)
    out[0x36:0x38] = p16(56)
    out[0x38:0x3A] = p16(1)
    out[0x3C:0x3E] = p16(5)
    out[0x48:0x50] = p64(base)
    out[0x50:0x58] = p64(base)
    out[0x58:0x60] = p64(size)
    out[0x60:0x68] = p64(size)
    out[code_off:] = code
    return bytes(out), code_off


def elf32(code, tier):
    base = 0x08048000
    if tier == "conservative":
        phoff, code_off = 52, 84
    else:
        phoff, code_off = 44, 76
    size = code_off + len(code)
    out = bytearray(size)
    out[0:16] = ident(32)
    out[0x10:0x12] = p16(2)
    out[0x12:0x14] = p16(3)
    out[0x14:0x18] = p32(1)
    out[0x18:0x1C] = p32(base + code_off)
    out[0x1C:0x20] = p32(phoff)
    out[0x28:0x2A] = p16(52)
    out[0x2A:0x2C] = p16(32)
    out[0x2C:0x2E] = p16(1)
    out[phoff + 0 : phoff + 4] = p32(1)
    out[phoff + 4 : phoff + 8] = p32(0)
    out[phoff + 8 : phoff + 12] = p32(base)
    out[phoff + 12 : phoff + 16] = p32(base)
    out[phoff + 16 : phoff + 20] = p32(size)
    out[phoff + 20 : phoff + 24] = p32(size)
    out[phoff + 24 : phoff + 28] = p32(5)
    out[phoff + 28 : phoff + 32] = p32(0x1000)
    out[code_off:] = code
    return bytes(out), code_off


def build(arch, behavior, tier):
    if arch == "x86_64":
        code_off = 0x78 if tier == "conservative" else 0x68
        code = x64_exit() if behavior == "exit" else x64_write(0x400000 + code_off)
        return elf64(code, tier)[0]
    code_off = 84 if tier == "conservative" else 76
    code = i386_exit() if behavior == "exit" else i386_write(0x08048000 + code_off)
    return elf32(code, tier)[0]


def write_output(path: pathlib.Path, data: bytes):
    path.write_bytes(data)
    path.with_suffix(path.suffix + ".hex" if path.suffix else ".hex").write_text(data.hex() + "\n", encoding="ascii")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main():
    parser = argparse.ArgumentParser(description="Emit tiny Linux ELF binaries.")
    parser.add_argument("--arch", choices=["x86_64", "i386"], required=True)
    parser.add_argument("--behavior", choices=["exit", "write"], required=True)
    parser.add_argument("--tier", choices=["conservative", "aggressive"], default="conservative")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    data = build(args.arch, args.behavior, args.tier)
    write_output(args.output, data)
    print(f"wrote {args.output} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
