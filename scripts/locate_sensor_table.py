#!/usr/bin/env python3
"""Find and decode the sensor readout-mode table in the ILCE-7CM2 coprocessor app.

The A7 IV open-gate designs change a handful of 16-bit fields in the sensor
driver: a window's active height, a vertical centering offset, an LC field and
a readout length. Those are not in appFw.so. On the A7C II they are in the
coprocessor application, `0700_part_image/dev/nflasha8_unpacked/cpapp-b.bin`
(18 MB), whose address range also matches the A7 IV design addresses.

Three structures sit next to each other there:

  1. a readout-mode table of 38-byte records, 19 little-endian u16 each:
     eight horizontal fields, eight vertical fields, three zero,
     where field 3 is the horizontal active width and field 12 the vertical
     active height. The table carries both 7008x4672 (the whole 3:2 sensor)
     and 7008x3942 (7008/3942 = 16:9, what the camera reads for 4K today).
  2. records pairing a vertical centering offset with an LC field. For the
     3942-high window the offset is 366, and (4672 - 3942) / 2 = 365, so the
     offset is what centres the short window in the full sensor.
  3. records carrying a readout length in line periods (2011 for that window).

This script locates all three by value and prints them with their file offsets,
so a design can name exact addresses. It only reads.

  python3 scripts/locate_sensor_table.py <p8>/cpapp-b.bin \
      --json evidence/sensor-table-a7cii-201.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct

RECORD = 38          # bytes per readout-mode record
FIELDS = 19          # u16 per record
H_ACTIVE = 3         # index of the horizontal active width
V_ACTIVE = 12        # index of the vertical active height
FULL_W, FULL_H = 7008, 4672
CROP_H = 3942        # the 16:9 window the camera reads for 4K
V_OFFSET = 366       # centres CROP_H in FULL_H
LC_FIELD = 403
READOUT = 2011


def u16_at(blob: bytes, value: int) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(value.to_bytes(2, "little")), blob)]


def decode(blob: bytes, off: int) -> dict:
    f = struct.unpack_from("<%dH" % FIELDS, blob, off)
    return {"offset": hex(off), "h": list(f[0:8]), "v": list(f[8:16]),
            "tail": list(f[16:19]),
            "width": f[H_ACTIVE], "height": f[V_ACTIVE]}


def find_table(blob: bytes) -> tuple[int, list[dict]]:
    """Anchor on a full-height record, then walk the table in both directions."""
    anchors = [o - H_ACTIVE * 2 for o in u16_at(blob, FULL_W)]
    base = None
    for cand in anchors:
        if cand < 0 or cand + RECORD > len(blob):
            continue
        rec = decode(blob, cand)
        if rec["width"] == FULL_W and rec["height"] == FULL_H:
            base = cand
            break
    if base is None:
        return -1, []

    def plausible(rec: dict) -> bool:
        return (64 <= rec["width"] <= 8192 and 64 <= rec["height"] <= 8192
                and rec["tail"] == [0, 0, 0])

    start = base
    while start - RECORD >= 0 and plausible(decode(blob, start - RECORD)):
        start -= RECORD
    end = base
    while end + 2 * RECORD <= len(blob) and plausible(decode(blob, end + RECORD)):
        end += RECORD
    return start, [decode(blob, o) for o in range(start, end + RECORD, RECORD)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=pathlib.Path, help="<p8>/cpapp-b.bin")
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if not args.image.is_file():
        print("no such image: %s" % args.image)
        return 2
    blob = args.image.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    print("%s  %#x bytes\nsha256 %s\n" % (args.image, len(blob), digest))

    base, records = find_table(blob)
    if base < 0:
        print("no record with %dx%d found; is this the coprocessor app?"
              % (FULL_W, FULL_H))
        return 1

    print("readout-mode table at %#x, %d records of %d bytes\n"
          % (base, len(records), RECORD))
    print("%-12s %-9s %-26s %s" % ("offset", "size", "horizontal", "vertical"))
    for rec in records:
        mark = ""
        if rec["height"] == FULL_H:
            mark = "   <- whole 3:2 sensor"
        elif rec["height"] == CROP_H:
            mark = "   <- 16:9 window (height field at %s)" % hex(
                int(rec["offset"], 16) + V_ACTIVE * 2)
        print("%-12s %4dx%-4d %-26s %s%s"
              % (rec["offset"], rec["width"], rec["height"],
                 rec["h"], rec["v"], mark))

    out = {"image": str(args.image), "sha256": digest, "size": len(blob),
           "table": {"offset": hex(base), "record_bytes": RECORD,
                     "fields": FIELDS, "records": records},
           "companions": {}}

    print("\ncompanion fields, same neighbourhood:")
    lo, hi = base - 0x400, base + 0x8000
    for name, value in (("v_offset_366", V_OFFSET), ("lc_field_403", LC_FIELD),
                        ("readout_2011", READOUT)):
        near = [o for o in u16_at(blob, value) if lo <= o < hi]
        out["companions"][name] = {"value": value,
                                   "offsets": [hex(o) for o in near]}
        print("  %-14s %5d  %s" % (name, value,
                                   " ".join(hex(o) for o in near) or "(none nearby)"))

    crop = [r for r in records if r["height"] == CROP_H]
    if crop:
        print("\nthe field a full-height design has to change:")
        for rec in crop:
            field = int(rec["offset"], 16) + V_ACTIVE * 2
            print("  %#010x  %04x -> %04x   (%d -> %d)"
                  % (field, CROP_H, FULL_H, CROP_H, FULL_H))
        out["crop_height_fields"] = [
            hex(int(r["offset"], 16) + V_ACTIVE * 2) for r in crop]

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2) + "\n")
        print("\nwrote %s" % args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
