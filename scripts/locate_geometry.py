#!/usr/bin/env python3
"""Search the extracted ILCE-7CM2 firmware for the numbers an open-gate design needs.

The published A7 IV kit changes a handful of 16-bit fields in sensor-geometry,
scaler and encoder tables. The same kinds of table exist on the A7C II, but at
addresses nobody has published, so every design has to start by finding them.

This prints, for each number of interest, how often its little-endian encoding
appears in the image and where. It is a starting point for the search, not an
answer: a 16-bit value appears for many unrelated reasons. Use --context to dump
the bytes around a hit, and --pattern to look for a byte string of your own.

Read-only, PC only.

  python3 scripts/locate_geometry.py <p15>/lib/appFw.so \
      --json evidence/geometry-probe-a7cii-201.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct

# name -> (value, why it matters). 16-bit unless the value needs more.
NUMBERS = {
    "sensor_active_width_7008": (7008, "full sensor width of the 33 MP sensor"),
    "sensor_active_height_4672": (4672, "full sensor height: what open gate wants to read out"),
    "uhd_width_3840": (3840, "3840: UHD width, and the open-gate 3:2 output width"),
    "uhd_height_2160": (2160, "2160: UHD height, replaced by 2560 in a 3:2 output"),
    "og_4k_height_2560": (2560, "3840x2560: the 3:2 output of the A7 IV kit's 4K state"),
    "og_57k_width_5760": (5760, "5760x3840: the A7 IV kit's real 5.7K state"),
    "og_57k_height_3840": (3840, "same as the UHD width; listed for completeness"),
    "a7iv_stream0_height_3942": (3942, "the A7 IV field the kit raises to 4672 (0x0f66)"),
    "a7iv_v_offset_366": (366, "the A7 IV V offset the kit zeroes (0x016e)"),
    "a7iv_readout_2011": (2011, "the A7 IV readout length in line periods (0x07db)"),
    "a7iv_lc_field6_403": (403, "the A7 IV LC field 6 value (0x0193)"),
}


# Hits inside these sections are never a geometry table: they are link-time
# metadata whose 24-byte records happen to contain any 16-bit value.
NOISE = (".rela.dyn", ".rela.plt", ".dynsym", ".dynstr", ".gnu.hash",
         ".gnu.version", ".gnu.version_r", ".symtab", ".strtab")


def sections(blob: bytes) -> list[tuple[str, int, int]]:
    """[(name, file offset, size)] of an ELF, or [] if this is not one."""
    if blob[:4] != b"\x7fELF":
        return []
    shoff = struct.unpack_from("<Q", blob, 0x28)[0]
    shent, shnum, shstrndx = struct.unpack_from("<HHH", blob, 0x3A)
    names_off = struct.unpack_from("<Q", blob, shoff + shstrndx * shent + 0x18)[0]
    out = []
    for i in range(shnum):
        base = shoff + i * shent
        name_at = names_off + struct.unpack_from("<I", blob, base)[0]
        end = blob.index(b"\0", name_at)
        _, offset, size = struct.unpack_from("<QQQ", blob, base + 0x10)
        out.append((blob[name_at:end].decode("latin1"), offset, size))
    return out


def section_of(secs: list[tuple[str, int, int]], offset: int) -> str:
    for name, start, size in secs:
        if name and start <= offset < start + size:
            return name
    return "?"


def hits(blob: bytes, pattern: bytes, limit: int,
         secs: list[tuple[str, int, int]] | None = None,
         skip_noise: bool = True,
         only: tuple[str, ...] = ()) -> list[tuple[int, str]]:
    found = []
    for m in re.finditer(re.escape(pattern), blob):
        name = section_of(secs, m.start()) if secs else "?"
        if only and name not in only:
            continue
        if skip_noise and name in NOISE:
            continue
        found.append((m.start(), name))
        if len(found) >= limit:
            break
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=pathlib.Path, help="usually <p15>/lib/appFw.so")
    ap.add_argument("--pattern", action="append", default=[],
                    help="extra byte string to look for, as hex")
    ap.add_argument("--limit", type=int, default=8, help="hits to list per pattern")
    ap.add_argument("--all-sections", action="store_true",
                    help="also list hits inside relocation and symbol tables")
    ap.add_argument("--section", action="append", default=[],
                    help="only list hits in this ELF section; repeat it. "
                         "Tables live in .rodata / .data, while .text hits are "
                         "immediates in code")
    ap.add_argument("--context", type=lambda s: int(s, 16), default=None,
                    help="dump 64 bytes around this offset and exit")
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if not args.image.is_file():
        print("no such image: %s" % args.image)
        return 2
    blob = args.image.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()

    if args.context is not None:
        start = max(0, args.context - 32)
        window = blob[start:start + 64]
        secs = sections(blob)
        print("section: %s" % section_of(secs, args.context))
        for off in range(0, len(window), 16):
            print("%#010x  %s" % (start + off, window[off:off + 16].hex(" ")))
        return 0

    secs = sections(blob)
    only = tuple(args.section)
    skip = not args.all_sections
    print("%s  %#x bytes\nsha256 %s" % (args.image, len(blob), digest))
    print("sections: %d%s%s\n" % (len(secs),
          "" if not skip else "  (hits in relocation/symbol tables left out)",
          "" if not only else "  (only %s)" % ", ".join(only)))
    out = {"image": str(args.image), "size": len(blob), "sha256": digest,
           "skipped_noise_sections": skip, "only_sections": list(only),
           "numbers": {}}

    width = max(len(n) for n in NUMBERS)
    for name, (value, why) in NUMBERS.items():
        pattern = value.to_bytes(2, "little")
        found = hits(blob, pattern, args.limit, secs, skip, only)
        total = len(re.findall(re.escape(pattern), blob))
        out["numbers"][name] = {
            "value": value, "le_hex": pattern.hex(), "total": total,
            "first": [{"offset": hex(o), "section": sec} for o, sec in found],
            "why": why}
        print("%-*s %5d (%s)  %6d total  %s" %
              (width, name, value, pattern.hex(), total,
               " ".join("%s[%s]" % (hex(o), sec) for o, sec in found)))

    for raw in args.pattern:
        pattern = bytes.fromhex(raw)
        found = hits(blob, pattern, args.limit, secs, skip, only)
        total = len(re.findall(re.escape(pattern), blob))
        out.setdefault("patterns", {})[raw] = {
            "total": total,
            "first": [{"offset": hex(o), "section": sec} for o, sec in found]}
        print("\npattern %s  %d total  %s" %
              (raw, total, " ".join("%s[%s]" % (hex(o), sec) for o, sec in found)))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2) + "\n")
        print("\nwrote %s" % args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
