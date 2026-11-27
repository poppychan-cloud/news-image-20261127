#!/usr/bin/env python3
"""Entrypoint: validate entry.png (1024x1024 PNG, at most 1 MiB) and copy
it to the output directory. No rendering here; draw.py renders.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    src = os.path.join(HERE, "entry.png")
    with open(src, "rb") as f:
        head = f.read(8)
    assert head == b"\x89PNG\r\n\x1a\n", "entry.png is not a PNG"
    size = os.path.getsize(src)
    assert size <= 1048576, f"entry.png is {size} bytes, over the 1 MiB limit"
    from PIL import Image
    im = Image.open(src)
    assert im.size == (1024, 1024), f"entry.png is {im.size}, not 1024x1024"
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, os.path.join(out_dir, "entry.png"))
    print(f"ok: entry.png 1024x1024, {size} bytes, copied to {out_dir}")


if __name__ == "__main__":
    main()
