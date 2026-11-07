# Reference plan: PATEK PHILIPPE Cubitus 5821/1A (45 mm steel, green embossed dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 103 (see `sources.md`). New model template (Cubitus); closest siblings: the Aquanaut 5167A / 5168G builds (rounded-octagon case, bezel window, fluted crown) and the Tudor / Omega steel bracelet builds.

## Target asset

Front relief GLB `models/watches/patek-58211a.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2691 RGBA PNG, the watch is 1405 x 2314 px incl. the crown | `patek-58211a_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights are the Aquanaut template's, back flat |

## Measured on this photo (continuous px of the native 1920 x 2691 frame)

| Item | Result |
| --- | --- |
| Anchor | listed 45 mm case width = left flank (median alpha edge rows 1100..1560, x 296.0) to right flank (rows 1100..1190 and 1400..1560, x 1657.4); 30.2444 px/mm; the photo is not centred on the pivot (case centre x 976.7) |
| Pivot | centre of the small hub disc (977.1, 1280.3); hour / minute / seconds-shaft centre lines within 1 px (camera tilt) |
| Case | squarish cushion: left and right walls (flanks) straight from row 1030 to 1590, shoulders at rows 608 (top) and 1978 (bottom) where the bracelet begins, crown guards on the right |
| Bezel | brushed rounded-octagon face inside a polished band; outer outline = traced polygon (top y 692, bottom y 1873, left x 383, right x 1571, corner chamfers traced from 1.8x crops); window face edge traced polygon (top y 828.5, bottom y 1726.5, left x 528) with a 25 to 30 px recessed rim |
| Dial | olive green dial with an embossed horizontal grid, applied baton indices (double bar at 12), minute dots, "PATEK PHILIPPE / GENEVE", date window at 3, "SWISS MADE" at 6: all in the native photo map, grid and print are texture only |
| Crown | one fluted crown at 3 o'clock, axis y 1292, radius 86 px, rows 1202..1382, from the flank (x 1657) to x 1699 |
| Bracelet | steel, brushed outer links with polished centre inserts; shingled links; joints top rows 606 / 452 / 339, ends 247; bottom 2157 / 2330 / 2440 / 2535, ends 2561 |
| Hands (about 10:09:30) | hour 302.84 deg (frame half 22.4 px, tip s 262), minute 50.81 deg (half 18, tip s 393.7), seconds 180 deg (shaft half 3.2, tip s 395 inside the 6 o'clock index, counterweight tail to s -155 up to GENEVE) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_patek_cubitus45.py` (copy of the Aquanaut step: measured polygon bezel, steel bracelet link pieces) |
| Prep | `pipeline/patek_cubitus45_prep.py` (copy of the Aquanaut 5168G prep: two-flank anchor, polygon bezel / window, steel map capped at 2048 px) |
| Comparison frame | 1400 px square at half the native scale (15.1222 px/mm) centred on the pivot (half-size photo pivot (488.55, 640.15) at (700, 700)), `config/presets/watch_kit_white_front_patek_cubitus45.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_cubitus45_prep 58211a   # -> config/watches/patek-cubitus45-58211a-trace.json, outputs/watches/patek-cubitus45-58211a/{dial_photo,steel_photo}.jpg
```
