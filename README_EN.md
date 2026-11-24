# A7C II open gate: field test kit (work in progress)

[日本語版](README.md)

> [!WARNING]
> Use at your own risk. The author accepts no liability for any damage caused by
> using this repository. Changing a camera's memory or firmware can leave it
> unable to boot and can destroy footage, calibration or settings, and it may
> affect warranty and repairs. Back up your camera's settings first, use a
> genuine battery, and do not pull USB mid-operation.

An attempt to build a kit that makes the Sony **ILCE-7CM2** (A7C II) on firmware
**Ver. 2.01** record the full 3:2 sensor area — "open gate" — as a **temporary,
memory-only** state.

> **Status: the sensor-side addresses are found; nothing has been applied to a
> camera.** Two candidate designs exist. What is verified about them is only
> that the firmware really holds those values at those addresses.

## What this is a port of

[ArcaneLantern/a7iv-open-gate-test](https://github.com/ArcaneLantern/a7iv-open-gate-test)
does this for the Sony A7 IV (6.02): it sends native helpers (`libJit_level*.so`)
to the camera over the USB service protocol and rewrites sensor-geometry, scaler
and encoder tables **for that power-on only**, giving 3840x2560 or 5760x3840
open-gate recordings. Pulling the battery returns the camera to stock.

This repository is **not a fork**. It is a new repository that rebuilds that
approach for the A7C II. All A7 IV results belong to their original authors; see
[REFERENCES.md](REFERENCES.md).

## Is it feasible on the A7C II? (today's assessment)

| Item | State |
| --- | --- |
| Sensor | the same 33 MP generation as the A7 IV (7008 x 4672), so the open-gate dimensions should map closely |
| Aspect / de-squeeze properties | present in the ILCE-7CM2 `appFw.so` (`0x02cf01fc ASPECT_RATIO`, the `DE_SQUEEZE_DISP` family) |
| A path for running native code | **not established.** It needs service level A (`adjCodeLevel == 3`), and whether an A7C II grants it is unconfirmed |
| Sensor geometry addresses | **found (2026-11-24).** The readout-mode table at 0xdd81d8 inside p8's `cpapp-b.bin`, carrying both 7008x4672 (the whole sensor) and today's 16:9 window 7008x3942. See [docs/SENSOR_TABLE.md](docs/SENSOR_TABLE.md) (Japanese) |
| Scaler / encoder addresses | **unknown.** None of the A7 IV addresses carry over |
| Applied to a camera | **not attempted** |

The third row is the real gate. The "run native code over USB" path the A7 IV kit
relies on corresponds, on the A7C II, to `0xff00` TestMode — the Jiritsu front end —
and that entry exists **only in service level A's dispatch table**. The reasoning
and a read-only probe live in the sibling repository
[sony-a7cii-shell-access](https://github.com/soralis0912/sony-a7cii-shell-access)
(`docs/ON_MEMORY.md`, `scripts/probe_service_level.py`).
**Until a camera reports level A, this repository cannot move forward.**

**One thing can be tried on a camera right now**: the de-squeeze display
backup properties. They need no native code and no design. The procedure is in
[docs/PROPERTY_EXPERIMENTS.md](docs/PROPERTY_EXPERIMENTS.md) (Japanese).

## What is here

```
designs/     designs (sets of byte patches); two candidates, old bytes verified
scripts/     verify_design.py       check a design's old bytes against the
                                    extracted firmware (PC only)
             locate_sensor_table.py find and decode the sensor readout-mode table
             locate_geometry.py     general probe for where dimensions occur
docs/        SENSOR_TABLE.md     the table that was found and why the candidate
                                 designs look the way they do
             DERIVATION.md       for each A7 IV step, what has to be identified on
                                 the A7C II
             DESIGN_FORMAT.md    the design JSON format
             PROPERTY_EXPERIMENTS.md
                                 the one experiment that needs no native code
evidence/    probe output, as a reproducible record
```

The host-side runners (Windows `.cmd`, macOS `.command`, an Android app) are
deliberately absent while there is nothing to apply. They come once there is.

## Using what exists today

Obtain the official update yourself and unpack it with the `a7cII` branch of
[fwtool.py](https://github.com/soralis0912/fwtool.py).

```bash
# look for candidate positions (tables live in .rodata / .data)
python3 scripts/locate_geometry.py \
  <p15>/lib/appFw.so --section .rodata --section .data --limit 6 \
  --json evidence/geometry-probe-a7cii-201.json

# inspect the bytes around one position
python3 scripts/locate_geometry.py <p15>/lib/appFw.so --context 3722680

# once a design exists, check it before a camera is involved
python3 scripts/verify_design.py designs/<name>.json --image <p15>/lib/appFw.so
```

`<p15>` is
`<fwtool.py>/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked`.

## What is deliberately not here

No Sony firmware, decrypted binaries, camera backups, serial numbers, decryption
keys or extracted proprietary files, and no binaries from other repositories
(including APKs and `libJit_*.so`). Only hashes, offsets and procedures.

No license is set yet. No upstream code has been copied; see
[REFERENCES.md](REFERENCES.md).

## Special thanks

- **[ArcaneLantern/a7iv-open-gate-test](https://github.com/ArcaneLantern/a7iv-open-gate-test)**
  — the template for this repository. It showed that open gate can be shot from a
  temporary, memory-only state on the A7 IV, and published that work as designs.
- **[Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware)**
  — showed that an ordinary USB cable and the service protocol can run native code
  on the camera.
- **[ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)**
  — handles the switch from mass storage to service mode, and implements the
  service protocol.
- **[DavidBuchanan314/fwtool.py](https://github.com/DavidBuchanan314/fwtool.py)**
  — unpacks the firmware needed for the analysis; its upstream
  [ma1co/fwtool.py](https://github.com/ma1co/fwtool.py) deserves credit too.
- **[leogenot/sony-a7iv-feature-research](https://github.com/leogenot/sony-a7iv-feature-research)**
  — documented the working service-mode routine on the A7 IV.
- **[soralis0912/sony-a7cii-feature-research](https://github.com/soralis0912/sony-a7cii-feature-research)**
  — the ILCE-7CM2 facts this repository builds on: extraction, product class,
  the property inventory, and service-mode access on a real camera.
