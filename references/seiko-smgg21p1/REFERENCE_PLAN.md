# Reference plan: Seiko SMGG21P1 (digital, octagon gear bezel, blue and grey insert, steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: delivered (round 2, 2026-11-06).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, official, transparent, 6432 × 6432 | `front_6432_transparent.png` | HAVE, primary for everything (upscaled: soft at full size) |
| 2 | Front, shop photo, 2230 × 4096 | `front_photo_2230x4096.png` | HAVE, cross-check |
| 3 | Back, 3/4 or side | none | GAP: heights estimated for the listed 10.64 mm |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | **37 mm** = bezel width across the flanks (tooth tips, listing). Checks: case ends 42.85 mm apart vs 43.5 listed; bracelet next to the case 20.8 mm vs 20 listed |
| Origin | Octagon centre (no hands) |
| Photo map | LCD, print and the blue/grey insert from the official image; no hands to remove |
| Bracelet | Five columns with the house curl; joints and column split from the image |

## Parts

| Part | True shape |
| --- | --- |
| Case | Block above and below the bezel: flat brushed top between creases at x = ±10.27 mm, side facets falling outward, polished edges; under the bezel on the flanks |
| Bezel | Polished octagon rim: U notches between flat teeth with rounded shoulders (2.06 mm pitch, 0.87 wide, 0.78 deep), a band sloping down to the insert, a dark 0.26 mm gap line between the teeth and the case |
| Insert and dial | Printed octagon ring (blue, grey at the upper left) around a white disc with the LCD |
| Pushers | Two plain cylinders at 4 and 8 (112.5° and 247.6°) |
| Bracelet | Brushed outer and centre links sharing joints at the case ends; polished links between, joints 1.73 mm nearer the case; pitch 4.35 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_smgg21_trace   # -> config/watches/seiko-smgg21p1-trace.json
python3 -B -m pipeline.seiko_smgg21_dial    # -> outputs/watches/seiko-smgg21p1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 92.135 px/mm; origin (3210, 2980) |
| Bezel support (top, diagonal, side) | 17.79, 18.69, 18.50 mm |
| Insert support (top, diagonal, side) | 16.19, 16.32, 16.00 mm; dial disc r 13.76 mm |
| Case ends | 21.51 (12) / 21.34 (6) mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-smgg21p1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: case block, notched octagon bezel, photo-mapped insert and LCD, octagon crystal, two pushers, five-column bracelet with the 7 mm house curl |
| 2 | 2026-11-06 | Bezel teeth re-measured (wider, rounder, 2.06 mm pitch) with a sloped inner band; dark gap line behind the teeth; case block creases and side facets (Irsyad) |
