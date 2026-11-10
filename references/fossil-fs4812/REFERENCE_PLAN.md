# Reference plan: Fossil Grant chronograph FS4812 (steel, black Roman dial, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/fossil-fs4812.glb`).
Own scripts, step and spec under this SKU; structure copied from [Zeppelin Z96903](../zeppelin-z96903/REFERENCE_PLAN.md).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2900 × 2900 | `front_2900x2900.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | `three_quarter_2000x3084.png` | HAVE, shapes only (bezel slope, pushers, lugs) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **44 mm** (listing). Checks at that scale: strap 20.91 mm (22 mm listed), lug to lug 52.5 mm (50 mm listed). The two checks disagree in opposite directions, so the listing case size stays |
| Origin | Hand pivot (1413, 1445); case circle centre is 0.19 / 0.14 mm off it, the model keeps the case on the pivot |
| Branch, file | `main` (as for the Zeppelin work on 2026-11-10); `models/watches/fossil-fs4812.glb` |
| Strap | Black leather from the front photo with the house 7 mm curl from the lug tips |
| Case, bezel | One polished lathe: flank to 5.6 mm, wide sloped bezel 18.14-22 mm. The black band on the bezel's left and right in the photo is a reflection, not a second colour |
| Lugs | Plain polished, sloped top, outline from the left flank (the right carries the pushers) |
| Crown side | Lobe between the pushers from the right silhouette; round pushers at 59.8° and 120.2°; knurled crown at 3 |
| Print, Roman numerals, logo, sub-dial scales, chrono track, minute track | Kept in the dial map; the minute-track flange is a cone. Hands, hubs and their shadows removed from the map |
| Hands | Polished sword hour and minute hands with white lume inserts (luminous per listing), polished chrono seconds needle with a tail, three polished sub-dial needles |

## Phase 1 outputs

```sh
python3 -B -m pipeline.fossil_fs4812_trace   # -> config/watches/fossil-fs4812-trace.json
python3 -B -m pipeline.fossil_fs4812_dial    # -> outputs/watches/fossil-fs4812/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 35.168 px/mm from the 44 mm case circle (left flank, bezel top and bottom) |
| Rings | bezel inner 18.14 mm, flange inner (flat dial edge) 15.55 mm |
| Lugs | leave the case at 15.0 mm, tips 26.5 (12) / 26.0 (6), mean 26.25 mm; strap half width 10.46 mm |
| Hands | hour 299.6°, minute 59.6°, chrono seconds 209.0°; sub-dials left 0.5°, right 359.0°, bottom 1.1° |
| Crown | 90°, radius 2.84 mm, knurl 22.24-23.86 mm |
| Pushers | 59.8° / 120.2°, cap radius 1.62 mm, 22.21-23.69 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/fossil-fs4812.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: polished case with the sloped bezel, plain lugs, crown-side lobe, pushers, knurled crown, photo dial with the minute-track cone, polished hands with lume inserts, black leather strap with the 7 mm curl |
