#!/usr/bin/env python3
"""Find the movie output-size table in the ILCE-7CM2 coprocessor app.

The sensor side is `locate_sensor_table.py`. This is the other end: a run of
u16 width/height pairs in `cpapp-b.bin` listing the sizes the pipeline can put
out. On 2.01 it already contains 3840x2560 - the 3:2 output an open-gate 4K
state wants - next to 3840x2160, 3840x2880 and 3840x3840, which look like the
16:9, 4:3 and 1:1 variants of the same width.

That matters: the size does not have to be invented, only selected.

Read-only, PC only.

  python3 scripts/locate_output_sizes.py <p8>/cpapp-b.bin
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

WIDTHS = (3840, 5760, 1920, 4608, 2048)
MIN_RUN = 3          # pairs sharing one width before it counts as a table
INTERESTING = {(3840, 2560): "3:2 at 4K width - what open gate needs",
               (3840, 2160): "16:9, the current 4K output",
               (3840, 2880): "4:3",
               (3840, 3840): "1:1",
               (5760, 3840): "the A7 IV kit's 5.7K state"}


def runs(blob: bytes, width: int):
    """Offsets where >= MIN_RUN consecutive u16 pairs all have this width."""
    needle = width.to_bytes(2, "little")
    out = []
    i = 0
    while True:
        at = blob.find(needle, i)
        if at < 0:
            break
        i = at + 1
        if at % 2:
            continue
        n = 0
        while at + 4 * n + 4 <= len(blob) and blob[at + 4 * n:at + 4 * n + 2] == needle:
            n += 1
        if n >= MIN_RUN:
            out.append((at, n))
            i = at + 4 * n
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=pathlib.Path, help="<p8>/cpapp-b.bin")
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if not args.image.is_file():
        print("no such image: %s" % args.image)
        return 2
    blob = args.image.read_bytes()
    print("%s  %#x bytes\nsha256 %s\n"
          % (args.image, len(blob), hashlib.sha256(blob).hexdigest()))

    out = {"image": str(args.image), "runs": []}
    for width in WIDTHS:
        for at, n in runs(blob, width):
            pairs = [struct.unpack_from("<2H", blob, at + 4 * k) for k in range(n)]
            print("%#010x  %d pairs of width %d" % (at, n, width))
            for k, (w, h) in enumerate(pairs):
                note = INTERESTING.get((w, h), "")
                print("   %#010x  %4dx%-5d %s" % (at + 4 * k, w, h, note))
            out["runs"].append({"offset": hex(at), "width": width,
                                "pairs": [{"offset": hex(at + 4 * k),
                                           "w": w, "h": h} for k, (w, h) in enumerate(pairs)]})
            print()

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2) + "\n")
        print("wrote %s" % args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
