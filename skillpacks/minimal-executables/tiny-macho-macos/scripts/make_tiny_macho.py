#!/usr/bin/env python3
import argparse
import hashlib
import os
import pathlib
import stat
import struct

MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
MH_EXECUTE = 2
MH_NOUNDEFS = 0x1
MH_PIE = 0x200000
LC_SEGMENT_64 = 0x19
LC_UNIXTHREAD = 0x5
LC_CODE_SIGNATURE = 0x1D
VM_PROT_READ = 0x1
VM_PROT_EXECUTE = 0x4
ARM_THREAD_STATE64 = 6
ARM_THREAD_STATE64_COUNT = 68
PAGEZERO_SIZE = 0x100000000
TEXT_VMADDR = 0x100000000
CS_PAGE_SIZE = 4096
CS_PAGE_BITS = 12
CSMAGIC_EMBEDDED_SIGNATURE = 0xFADE0CC0
CSMAGIC_CODEDIRECTORY = 0xFADE0C02
CS_ADHOC = 0x2
CS_LINKER_SIGNED = 0x20000
CS_HASHTYPE_SHA256 = 2
CS_EXECSEG_MAIN_BINARY = 0x1
MSG = b"hi\n"


def p32(n):
    return struct.pack("<I", n & 0xFFFFFFFF)


def p64(n):
    return struct.pack("<Q", n & 0xFFFFFFFFFFFFFFFF)


def p32be(n):
    return struct.pack(">I", n & 0xFFFFFFFF)


def p64be(n):
    return struct.pack(">Q", n & 0xFFFFFFFFFFFFFFFF)


def round_up(n, align):
    return (n + align - 1) & ~(align - 1)


def movz_x(rd, imm16):
    return p32(0xD2800000 | ((imm16 & 0xFFFF) << 5) | rd)


def svc_0x80():
    return p32(0xD4001001)


def adr_x(rd, imm):
    imm &= (1 << 21) - 1
    return p32(0x10000000 | ((imm & 3) << 29) | ((imm >> 2) << 5) | rd)


def exit_code():
    return movz_x(0, 0) + movz_x(16, 1) + svc_0x80()


def write_code(code_vaddr):
    ins = [movz_x(0, 1), b"\0\0\0\0", movz_x(2, len(MSG)), movz_x(16, 4), svc_0x80(), exit_code()]
    code = bytearray(b"".join(ins))
    msg_off = len(code)
    code[4:8] = adr_x(1, code_vaddr + msg_off - (code_vaddr + 4))
    code += MSG
    return bytes(code)


def segname(name):
    raw = name.encode("ascii")
    return raw + bytes(16 - len(raw))


def segment(name, vmaddr, vmsize, fileoff, filesize, maxprot, initprot):
    return (
        p32(LC_SEGMENT_64) + p32(72) + segname(name) + p64(vmaddr) + p64(vmsize)
        + p64(fileoff) + p64(filesize) + p32(maxprot) + p32(initprot) + p32(0) + p32(0)
    )


def code_signature_command(dataoff, datasize):
    return p32(LC_CODE_SIGNATURE) + p32(16) + p32(dataoff) + p32(datasize)


def thread_command(pc):
    state = bytearray(ARM_THREAD_STATE64_COUNT * 4)
    pc_off = 29 * 8 + 8 + 8 + 8
    state[pc_off : pc_off + 8] = p64(pc)
    return p32(LC_UNIXTHREAD) + p32(16 + len(state)) + p32(ARM_THREAD_STATE64) + p32(ARM_THREAD_STATE64_COUNT) + bytes(state)


def code_signature(signed_data, ident):
    nslots = len(signed_data) // CS_PAGE_SIZE
    ident_bytes = ident.encode("ascii") + b"\0"
    cd_size = 88
    ident_off = cd_size
    hash_off = ident_off + len(ident_bytes)
    cd_len = hash_off + nslots * 32
    super_size = 20
    total = super_size + cd_len
    out = bytearray()
    out += p32be(CSMAGIC_EMBEDDED_SIGNATURE) + p32be(total) + p32be(1)
    out += p32be(0) + p32be(super_size)
    out += p32be(CSMAGIC_CODEDIRECTORY) + p32be(cd_len) + p32be(0x20400)
    out += p32be(CS_ADHOC | CS_LINKER_SIGNED) + p32be(hash_off) + p32be(ident_off)
    out += p32be(0) + p32be(nslots) + p32be(len(signed_data))
    out += bytes([32, CS_HASHTYPE_SHA256, 0, CS_PAGE_BITS])
    out += p32be(0) + p32be(0) + p32be(0) + p32be(0)
    out += p64be(0) + p64be(0) + p64be(len(signed_data)) + p64be(CS_EXECSEG_MAIN_BINARY)
    out += ident_bytes
    for off in range(0, len(signed_data), CS_PAGE_SIZE):
        out += hashlib.sha256(signed_data[off : off + CS_PAGE_SIZE]).digest()
    return bytes(out)


def macho(code, aggressive, page_size, ident):
    thread_size = 16 + ARM_THREAD_STATE64_COUNT * 4
    cmd_size = 72 + 72 + thread_size + 72 + 16
    header_size = 32 + cmd_size
    state_fileoff = 32 + 72 + 72 + 16
    code_off = state_fileoff if aggressive else header_size
    payload = max(header_size, code_off + len(code))
    sigoff = round_up(payload, page_size)
    sig_probe = code_signature(bytes(sigoff), ident)
    text_vmsize = sigoff
    linkedit_vmsize = round_up(len(sig_probe), page_size)
    pc = TEXT_VMADDR + code_off
    header = (
        p32(MH_MAGIC_64) + p32(CPU_TYPE_ARM64) + p32(0) + p32(MH_EXECUTE)
        + p32(5) + p32(cmd_size) + p32(MH_NOUNDEFS | MH_PIE) + p32(0)
    )
    commands = bytearray()
    commands += segment("__PAGEZERO", 0, PAGEZERO_SIZE, 0, 0, 0, 0)
    commands += segment("__TEXT", TEXT_VMADDR, text_vmsize, 0, sigoff, VM_PROT_READ | VM_PROT_EXECUTE, VM_PROT_READ | VM_PROT_EXECUTE)
    commands += thread_command(pc)
    commands += segment("__LINKEDIT", TEXT_VMADDR + sigoff, linkedit_vmsize, sigoff, len(sig_probe), VM_PROT_READ, VM_PROT_READ)
    commands += code_signature_command(sigoff, len(sig_probe))
    out = bytearray(header + commands)
    if aggressive:
        out[code_off : code_off + len(code)] = code
    else:
        out += code
    payload_size = len(out)
    out += bytes(sigoff - len(out))
    sig = code_signature(bytes(out), ident)
    out += sig
    return bytes(out), payload_size, sigoff, len(sig)


def write_artifact(path, data):
    path.write_bytes(data)
    path.with_suffix(path.suffix + ".hex" if path.suffix else ".hex").write_text(data.hex() + "\n", encoding="ascii")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_dynamic_templates(out):
    (out / "exit_dynamic.s").write_text(""".globl _start\n.p2align 2\n_start:\n    mov x0, #0\n    mov x16, #1\n    svc #0x80\n""", encoding="ascii")
    (out / "write_dynamic.s").write_text(""".globl _start\n.p2align 2\n_start:\n    mov x0, #1\n    adr x1, msg\n    mov x2, #3\n    mov x16, #4\n    svc #0x80\n    mov x0, #0\n    mov x16, #1\n    svc #0x80\nmsg:\n    .ascii \"hi\\n\"\n""", encoding="ascii")
    (out / "build_dynamic.sh").write_text("""#!/usr/bin/env sh\nset -eu\nclang -arch arm64 -Wl,-e,_start -Wl,-dead_strip exit_dynamic.s -o tiny_exit\nclang -arch arm64 -Wl,-e,_start -Wl,-dead_strip write_dynamic.s -o tiny_write\n""", encoding="ascii")
    os.chmod(out / "build_dynamic.sh", 0o755)


def main():
    parser = argparse.ArgumentParser(description="Emit tiny macOS arm64 Mach-O artifacts.")
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--emit", choices=["static", "dynamic", "all"], default="all")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    page_size = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 16384
    if args.emit in ("static", "all"):
        rows = []
        for name, behavior, codefn in (("tiny_exit_static", "exit", lambda off: exit_code()), ("tiny_write_static", "write", write_code)):
            code_off = 32 + 72 + 72 + 16
            code = codefn(TEXT_VMADDR + code_off)
            data, payload, sigoff, sigsize = macho(code, True, page_size, name)
            write_artifact(args.output_dir / name, data)
            rows.append((name, behavior, payload, sigoff, sigsize, len(data)))
        (args.output_dir / "sizes.txt").write_text(
            "artifact,behavior,payload_bytes,signature_offset,signature_bytes,file_bytes\n"
            + "\n".join("{},{},{},{},{},{}".format(*row) for row in rows) + "\n",
            encoding="ascii",
        )
    if args.emit in ("dynamic", "all"):
        write_dynamic_templates(args.output_dir)
    print(f"wrote Mach-O artifacts to {args.output_dir}")


if __name__ == "__main__":
    main()
