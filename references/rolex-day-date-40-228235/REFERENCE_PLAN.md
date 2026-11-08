# Reference plan: ROLEX Day-Date 40 228235 (40 mm Everose gold, fluted bezel, chocolate dial, President bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL: Day-Date 40 (fluted bezel + President bracelet); the 228238 row is skipped, so no later variants are queued.

## Target asset

Front relief GLB `models/watches/rolex-228235.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, fluted bezel with 152 real facets, crystal, dial plate, Cyclops lens, three hands at different heights, hub, fluted crown, President bracelet links as barrels / flat pieces and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 957 x 1828 px incl. the crown | `rolex-228235_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Datejust / Submariner Rolex templates (case thickness about 8 mm real), back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame; the full numbers are in the `note` of `config/watches/rolex-daydate40-228235-measure.json`)

| Item | Result |
| --- | --- |
| Anchor | the listed 40 mm case = 2 x (case centre x 960.0 - fluted-bezel flank x 511.6) = 896.8 px, 22.42 px/mm; lug to lug 47.9 mm |
| Pivot | hub screw (960, 1424), hub disc radius 17 px; rings centred (959.1, 1424.4) |
| Rings (px) | dial 339.5, rehaut edge 352, grey flange to 376.2, fluted face boundaries long 384.5 .. 439.4 / short 389.5 .. 436.1, case flank 447.5 |
| Bezel | 76 flutes = 152 facets of 2.368 deg (FFT / edge-peak count), zig-zag in and out |
| Dial | chocolate sunburst; applied Everose Roman numerals and bars / batons, ROLEX coronet, OYSTER PERPETUAL / DAY-DATE, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, day-of-week arc window at 12 showing MONDAY, date window 28 with a Cyclops at 3; all native photo map |
| Hands (about 10:09:30) | hour 305.5 deg (baton, tip 8.6 mm, tail 2.6), minute 63.55 deg (13.9, 2.6), seconds 186.3 deg (needle 14.1 mm, tail 4.5); gold with a dark facet, drawn from edge scans |
| Crown | fluted, axis 0.58 mm below the pivot, radius 3.03 mm, x 20.07 .. 22.61 mm |
| Bracelet | President: outer brushed semicircular links (joints top 695.5 / 740 / 813.5, bottom 2103 / 2322 / 2405.5 / 2466.5 / 2506) and polished centre links with dark gaps (top 706 / 752 / 832, bottom 2001 / 2124 / 2234 / 2327 / 2395 / 2445 / 2489), ends 686 / 2513, column lines x 858 / 1062 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_rolex_daydate40.py` (copy of the Datejust 41 fluted-bezel step; President bracelet with sine-arch outer links and explicit centre gaps) |
| Prep | new `pipeline/rolex_daydate40_prep.py` (copy of the Datejust 41 prep; hands drawn as polygons) |
| Comparison frame | 1280 px square at half the native scale (11.21 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_rolex_daydate40.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daydate40_prep 228235   # -> config/watches/rolex-daydate40-228235-trace.json, outputs/watches/rolex-daydate40-228235/{dial_photo,steel_photo}.jpg
```
