#!/usr/bin/env python3
"""Check a design's `old` bytes against the extracted ILCE-7CM2 firmware.

A design is a list of byte patches, each naming the offset it applies at and the
bytes it expects to find there. Before anything is sent to a camera, every
`old` must match the firmware image the design was written for; a design whose
`old` bytes are not there is for another firmware, another model, or simply
wrong, and applying it would corrupt unrelated code.

This runs entirely on the PC. It never touches a camera.

  python3 scripts/verify_design.py designs/<name>.json \
      --image <p15>/lib/appFw.so
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys


def load(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text())
    if "patches" not in data:
        raise SystemExit("%s has no \"patches\" list" % path)
    return data


def check(design: dict, images: dict[str, bytes]) -> int:
    bad = 0
    for i, patch in enumerate(design.get("patches", []), 1):
        where = patch.get("where", "file")
        note = patch.get("note", "")
        addr_text = patch.get("addr")
        if addr_text is None or "old" not in patch or "new" not in patch:
            print("%2d  INVALID   missing addr/old/new" % i)
            bad += 1
            continue
        addr = int(str(addr_text), 16)
        old = bytes.fromhex(patch["old"])
        new = bytes.fromhex(patch["new"])
        label = "%2d  %-10s %#010x %-14s" % (i, patch.get("kind", "?"), addr, patch["old"])

        if len(new) != len(old):
            print("%s SIZE      new is %d bytes, old is %d" % (label, len(new), len(old)))
            bad += 1
            continue
        image = images.get(where)
        if image is None:
            print("%s NO IMAGE  nothing given for where=%r" % (label, where))
            bad += 1
            continue
        if addr + len(old) > len(image):
            print("%s OUTSIDE   image is %#x bytes" % (label, len(image)))
            bad += 1
            continue
        found = image[addr:addr + len(old)]
        if found == old:
            print("%s ok        -> %-14s %s" % (label, patch["new"], note))
        else:
            print("%s MISMATCH  found %s   %s" % (label, found.hex(), note))
            bad += 1
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("design", type=pathlib.Path)
    ap.add_argument("--image", type=pathlib.Path, action="append", default=[],
                    help="image the patches apply to; repeat as where=path to "
                         "name a target other than \"file\"")
    args = ap.parse_args()

    images: dict[str, bytes] = {}
    for item in args.image:
        text = str(item)
        where, _, path_text = text.partition("=")
        if not path_text:
            where, path_text = "file", text
        path = pathlib.Path(path_text)
        if not path.is_file():
            print("no such image: %s" % path, file=sys.stderr)
            return 2
        blob = path.read_bytes()
        images[where] = blob
        print("%-6s %s  %#x bytes  sha256 %s" %
              (where, path, len(blob), hashlib.sha256(blob).hexdigest()))
    if not images:
        print("give at least one --image", file=sys.stderr)
        return 2

    design = load(args.design)
    print("\ndesign: %s  (%d patches)\n" % (design.get("design", args.design.stem),
                                            len(design.get("patches", []))))
    bad = check(design, images)
    print()
    if bad:
        print("%d patch(es) do not match. This design is NOT for these images." % bad)
        return 1
    print("every old matches. The design is consistent with these images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
