#!/usr/bin/env python3
"""Validate entry.png and copy it to /output.

This is the entrypoint the grader runs. Stdlib only: it checks the PNG
signature, the 1024x1024 size and the 1 MiB limit, then copies the image
to /output/entry.png. No network, no randomness.
"""
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
MAX_BYTES = 1024 * 1024


def main():
    with open(SRC, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        print("error: entry.png is not a PNG file", file=sys.stderr)
        return 1
    width, height = struct.unpack(">II", head[16:24])
    if (width, height) != (1024, 1024):
        print(f"error: entry.png is {width}x{height}, expected 1024x1024",
              file=sys.stderr)
        return 1
    size = os.path.getsize(SRC)
    if size > MAX_BYTES:
        print(f"error: entry.png is {size} bytes, over the 1 MiB limit",
              file=sys.stderr)
        return 1
    outdir = "/output"
    os.makedirs(outdir, exist_ok=True)
    shutil.copyfile(SRC, os.path.join(outdir, "entry.png"))
    print(f"ok: entry.png {width}x{height}, {size} bytes -> {outdir}/entry.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
