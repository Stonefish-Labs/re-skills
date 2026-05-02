#!/usr/bin/env python3
import argparse
import os
import pathlib
import stat
import struct

TINYPE_X64_HEX = """
4d5a000050450000648601004d657373616765426f785700800022000b02
000002010000ff256a0000000000fc0000000a0000000000004001000000
0400000004000000488d52b8ebda000006000000000000000c010000c400
000000000000020060810000100000000000001000000000000000001000
000000005553455233322e646c6c00000200000041b940002400ebb0f400
0000180000002e004c8d42c8ebe802010000940000000201000094000000
410042004300440045004600470000003dd8afdc2000540069006e007900
5000450020006f006e002000570069006e0064006f007700730020003100
30000000080100000000000031c9eb9e7c000000940000000a000000
"""


def p16(n):
    return struct.pack("<H", n)


def p32(n):
    return struct.pack("<I", n)


def p64(n):
    return struct.pack("<Q", n)


def align(data, size):
    return data + bytes((-len(data)) % size)


def pe_baseline(arch):
    is64 = arch == "x86_64"
    machine = 0x8664 if is64 else 0x14C
    opt_size = 0xF0 if is64 else 0xE0
    code = b"\x31\xc0\xc3" if not is64 else b"\x31\xc0\xc3"
    raw_ptr = 0x200
    image_base = 0x140000000 if is64 else 0x400000
    text_rva = 0x1000
    raw_size = 0x200

    dos = bytearray(0x80)
    dos[0:2] = b"MZ"
    dos[0x3C:0x40] = p32(0x80)
    out = bytearray(dos)
    out += b"PE\0\0"
    out += p16(machine) + p16(1) + p32(0) + p32(0) + p32(0) + p16(opt_size)
    out += p16(0x022 if is64 else 0x102)
    if is64:
        out += p16(0x20B) + b"\0\0" + p32(raw_size) + p32(0) + p32(0)
        out += p32(text_rva) + p32(text_rva) + p64(image_base)
        out += p32(0x1000) + p32(0x200)
        out += p16(6) + p16(0) + p16(0) + p16(0) + p16(6) + p16(0)
        out += p32(0) + p32(0x2000) + p32(raw_ptr) + p32(0)
        out += p16(3) + p16(0) + p64(0x100000) + p64(0x1000)
        out += p64(0x100000) + p64(0x1000) + p32(0) + p32(16)
    else:
        out += p16(0x10B) + b"\0\0" + p32(raw_size) + p32(0) + p32(0)
        out += p32(text_rva) + p32(text_rva) + p32(0x2000) + p32(image_base)
        out += p32(0x1000) + p32(0x200)
        out += p16(4) + p16(0) + p16(0) + p16(0) + p16(4) + p16(0)
        out += p32(0) + p32(0x2000) + p32(raw_ptr) + p32(0)
        out += p16(3) + p16(0) + p32(0x100000) + p32(0x1000)
        out += p32(0x100000) + p32(0x1000) + p32(0) + p32(16)
    out += bytes(16 * 8)
    out += b".text\0\0\0" + p32(len(code)) + p32(text_rva) + p32(raw_size) + p32(raw_ptr)
    out += p32(0) + p32(0) + p16(0) + p16(0) + p32(0x60000020)
    out = bytearray(align(bytes(out), raw_ptr))
    out += code + bytes(raw_size - len(code))
    return bytes(out)


def write_output(path, data):
    path.write_bytes(data)
    path.with_suffix(path.suffix + ".hex" if path.suffix else ".hex").write_text(data.hex() + "\n", encoding="ascii")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main():
    parser = argparse.ArgumentParser(description="Emit tiny Windows PE fixtures and baselines.")
    parser.add_argument("--arch", choices=["i386", "x86_64"], required=True)
    parser.add_argument("--variant", choices=["baseline", "tinype-final"], default="baseline")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.variant == "tinype-final":
        if args.arch != "x86_64":
            raise SystemExit("tinype-final fixture is PE32+ x86_64 only")
        data = bytes.fromhex("".join(TINYPE_X64_HEX.split()))
    else:
        data = pe_baseline(args.arch)
    write_output(args.output, data)
    print(f"wrote {args.output} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
