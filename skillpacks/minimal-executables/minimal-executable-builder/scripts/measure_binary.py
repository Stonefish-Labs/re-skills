#!/usr/bin/env python3
import argparse
import collections
import json
import math
import pathlib


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    total = len(data)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def measure(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(data),
        "entropy": round(entropy(data), 6),
        "sha256": __import__("hashlib").sha256(data).hexdigest(),
        "prefix16": data[:16].hex(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure tiny executable artifacts.")
    parser.add_argument("paths", nargs="+", type=pathlib.Path)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    results = [measure(path) for path in args.paths]
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for item in results:
        print(
            f"{item['bytes']:>8} bytes  entropy={item['entropy']:.6f}  "
            f"sha256={item['sha256']}  {item['path']}"
        )


if __name__ == "__main__":
    main()
