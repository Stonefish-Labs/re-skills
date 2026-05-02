#!/usr/bin/env python3
import argparse
import pathlib
import re


def clean_hex(text: str) -> str:
    value = re.sub(r"[^0-9a-fA-F]", "", text)
    if len(value) % 2:
        raise ValueError("hex input has an odd number of digits")
    return value.lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert binaries to hex or hex back to binaries.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    to_hex = sub.add_parser("to-hex")
    to_hex.add_argument("binary", type=pathlib.Path)
    to_hex.add_argument("hexfile", type=pathlib.Path)

    from_hex = sub.add_parser("from-hex")
    from_hex.add_argument("hexfile", type=pathlib.Path)
    from_hex.add_argument("binary", type=pathlib.Path)

    verify = sub.add_parser("verify")
    verify.add_argument("binary", type=pathlib.Path)
    verify.add_argument("hexfile", type=pathlib.Path)

    args = parser.parse_args()
    if args.cmd == "to-hex":
        args.hexfile.write_text(args.binary.read_bytes().hex() + "\n", encoding="ascii")
    elif args.cmd == "from-hex":
        args.binary.write_bytes(bytes.fromhex(clean_hex(args.hexfile.read_text(encoding="ascii"))))
    else:
        expected = bytes.fromhex(clean_hex(args.hexfile.read_text(encoding="ascii")))
        actual = args.binary.read_bytes()
        if actual != expected:
            raise SystemExit(f"roundtrip mismatch: {args.binary} != {args.hexfile}")
        print(f"ok: {args.binary} matches {args.hexfile}")


if __name__ == "__main__":
    main()
