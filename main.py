#!/usr/bin/env python3
"""Validate entry.png (PNG, 1024x1024, <=1 MiB) and copy it to the output dir.

Output dir comes from MAKEFUN_OUTPUT_DIR (default ./output).
Usage: python3 main.py
"""
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES = 1024 * 1024


def main():
    src = os.path.join(HERE, "entry.png")
    if not os.path.exists(src):
        print("FAIL: entry.png missing — run draw.py first", file=sys.stderr)
        return 1
    with open(src, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        print("FAIL: not a PNG file", file=sys.stderr)
        return 1
    w, h = struct.unpack(">II", head[16:24])
    if (w, h) != (1024, 1024):
        print(f"FAIL: size is {w}x{h}, expected 1024x1024", file=sys.stderr)
        return 1
    size = os.path.getsize(src)
    if size > MAX_BYTES:
        print(f"FAIL: {size} bytes exceeds 1 MiB", file=sys.stderr)
        return 1
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(HERE, "output")
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, "entry.png")
    shutil.copyfile(src, dst)
    print(f"OK: entry.png {w}x{h} {size} bytes -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
