# Reference plan: ROLEX Sky-Dweller 42 336934 (42 mm steel, white-gold fluted bezel, blue dial, annual calendar ring, Cyclops date, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL: this is the Sky-Dweller 42 template (no further Sky-Dweller rows are queued).

## Target asset

Front relief GLB `models/watches/rolex-336934.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, polished flange, chamfer and 70 real flutes of the white-gold bezel, crystal, dial plate with rehaut, Cyclops lens, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1033 x 1879 px incl. the crown | `rolex-336934_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Datejust 41 template, flatter bezel, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | the widest part of the head at the pivot row is the 42 mm case flank: left edge x 479.3, case centre x 960.0 -> 961.4 px, 22.890 px/mm; cross-checks: bracelet at the lugs 490 px = 21.4 mm, lug rows 880..2020 = 49.8 mm, crown diameter 6.9 mm |
| Pivot | hub screw (960, 1425) |
| Circles (parallax: lower layers appear lower) | dial edge r 355.5 about (959.5, 1429.7); rehaut / flange line r 367.8 and flange outer r 396.9 about (959.3, 1424.4); flute inner tips 398.5 / notches 412.0 (same centre); flute outer ends 465.3 / 463.4 about (958.8, 1430.2); case flank 480.7 |
| Bezel | polished flange, black chamfer triangles, 70 flutes = 140 flat facets of 2.571 deg (FFT, N = 140), alternate boundaries long / short at both ends, a boundary lies at 9 and 12 o'clock |
| Dial | blue sunburst: applied baton indices (12 as a square), ROLEX coronet with a red triangle, SKY-DWELLER / OYSTER PERPETUAL / SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, annual calendar ring (24 h numerals, hour dots) with the red pointer at 8 o'clock, Cyclops date window |
| Cyclops | barrel lens about 7.3 x 5.8 mm over the date window (centre 1211.5, 1422), date numeral 28 magnified |
| Hands | hour 305.3 deg (tip 9.4 mm, tail 2.7), minute 69.1 deg (tip 14.3 mm), seconds 191.9 deg (tip 14.7 mm, counterweight 3.9); outlines traced / measured by the prep |
| Crown | fluted, no guards: axis y 1440, radius 79 px (3.45 mm), x 1441..1511 |
| Bracelet | Oyster, three columns, column lines x 854.8 / 1063.5; outer joints top 748.5, bottom 2187 / 2368 / 2484.5; centre top 861 / 719, bottom 2045 / 2244 / 2406 / 2520; ends 659 / 662 / 2537 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_rolex_skydweller42.py` (copy of the Datejust 41 step: three ring centres, rehaut ribbon, 70 flutes) |
| Prep | new `pipeline/rolex_skydweller42_prep.py` (B - R hand colour test for the blue dial, outer bezel centre, native maps) |
| Comparison frame | 1280 px square at half the native scale (11.4453 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_rolex_skydweller42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_skydweller42_prep 336934   # -> config/watches/rolex-skydweller42-336934-trace.json, outputs/watches/rolex-skydweller42-336934/{dial_photo,steel_photo}.jpg
```
