# Reference plan: PATEK PHILIPPE Aquanaut 5168G (42.2 mm white gold, green embossed dial, green composite rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 102 (see `sources.md`). Follower of the Aquanaut template built for the [5167A-001](../patek-aquanaut-5167a-001/REFERENCE_PLAN.md); the blue 5168G (row 104) follows this one.

## Target asset

Front relief GLB `models/watches/patek-5168g-green.glb` (tracker rule: lowercase brand + normalized SKU, variant appended because the SKU repeats), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2691 RGBA PNG, the watch is 1370 x 2171 px incl. the crown | `patek-5168g-green_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights are the template's (real case thickness about 8.1 mm), back flat |

## Measured on this photo (continuous px of the native 1920 x 2691 frame)

| Item | Result |
| --- | --- |
| Anchor | listed 42.2 mm case = left flank of the case (median alpha edge over rows 1325..1385, x 329.17) to the notch wall of the crown at 2 x pivot x - flank = 1588.8; 29.8498 px/mm |
| Pivot | centre of the white seconds hub disc (959.0, 1354.5); seconds shaft within 0.1 px, hour / minute lume lines within 1.5 px |
| Bezel | brushed rounded-octagon face inside a polished band of about 40 px; outer outline = superellipse centred (959, 1354.75), half axes 629.83 x 622.25 px, exponent 2.25 (checked on the silhouette at rows 1100..1600 within 3 px), cut back to the silhouette; window scanned on 720 rays (15.8 to 17.2 mm from the pivot), polished chamfer about 14 px |
| Dial | khaki green embossed "globe grid" dial, applied arabic numerals and luminous batons, minute track on a sloped flange, date window at 3, "SWISS MADE" at 6: all in the native photo map, the grid is texture only |
| Crown | one fluted crown at 3 o'clock, axis y 1356.5, radius 83.5 px, rows 1273..1440, from the notch wall to x 1698.9 (116 px), larger and flatter-ended than the 5167A's |
| Lugs | integrated; top corners start at row 612, bottom tips end at row 2120 (lug to lug about 50.5 mm); strap inner walls flare / taper in the lug zone (top left 624 -> 620, right 1288 -> 1295 over rows 620..720; bottom left 626 -> 628, right 1300 -> 1296) |
| Strap | khaki green composite rubber, about 22.5 mm between the lugs, rounded ends (silhouette rows 384 top, 2554 bottom); embossed grid pad texture only |
| Hands (about 10:09:30) | hour 302.6 deg (frame half 28 px, lume half 15.2, arrow apex s 310), minute 50.6 deg (frame half 24.7, lume 14.7, apex s 437), seconds 180.28 deg (shaft half 2.7, tip s 448 inside the 6 o'clock index, counterweight tail to s 153); hour-hand base disc radius 40 px, white seconds hub 21 px |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | the template's `pipeline/steps/watch_patek_aquanaut40.py`, read-only (spec driven, no code change needed) |
| Prep | `pipeline/patek_aquanaut42_prep.py`: copy of the 5167A prep with the model name `patek-aquanaut42` and straight (flaring) strap inner walls; generic over the 5168G variants |
| Comparison frame | 1280 px square at half the native scale (14.9249 px/mm) centred on the pivot (half-size photo pivot (479.5, 677.25) at (640, 640)), `config/presets/watch_kit_white_front_patek_aquanaut42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_aquanaut42_prep 5168g-green 5168g-green   # -> config/watches/patek-aquanaut42-5168g-green-trace.json, outputs/watches/patek-aquanaut42-5168g-green/{dial_photo,steel_photo}.jpg
```
