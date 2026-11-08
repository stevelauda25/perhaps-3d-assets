# Reference plan: ROLEX GMT-Master II 126720VTNR (40 mm steel, black dial, green and black Cerachrom 24 h bezel, left crown, date with Cyclops lens at 9, GMT hand, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). ADAPT of the GMT-Master II 40 template built for the 126710BLNR (`../rolex-gmt-master-ii-126710blnr/baseline/BASELINE.md`, section "Template for the next GMT-Master II variants"), with a mirror option for the crown side and the Oyster bracelet layout of the Submariner Date 126610LN.

## Target asset

Front relief GLB `models/watches/rolex-126720vtnr.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, 24 h ceramic bezel insert, polished rim, 60-flute coin-edge ring, crystal, dial plate, Cyclops lens above the crystal, four hands at different heights, hub, fluted crown on the left, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1017 x 1832 px incl. the crown | `rolex-126720vtnr_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | The alpha mask mirrored about x (x' = 1919 - x) equals the 126710BLNR mask over the head (0 px differ by more than 60/255 in rows 1000..1900; 7634 px only in the bracelet and lug tops). Right coin-edge tip at the pivot row x 1422.9, bracelet centre x 960.0 -> 40 mm = 925.8 px, 23.145 px/mm; pivot = hub screw (960.7, 1424.3) -> (960, 1424); ring centre (959.9, 1424.0); rings (px, the blnr camera, re-fitted here): dial 309.3, crystal / flange 351, bezel inner edge 366.4, insert outer 436.05, rim outer 442.9, tips 462.7 |
| Dial | Same dial and hands as the 126710BLNR photo (pixel difference only at the GMT hand colour and the date window): round lume indices at 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11, bar at 3, long bar at 6, triangle at 12, no index at 9 (date window), ROLEX coronet, OYSTER PERPETUAL DATE, GMT-MASTER II, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut ROLEX engraving |
| Bezel | 24 h scale: upper half black, lower half green with a light green facet, numerals, dots, lume triangle at 12, polished rim, 60 coin-edge flutes |
| Date window / Cyclops | at 9 o'clock: rounded lens (flat top y 1355, bottom y 1487.5, bowed sides, x 665..831), white window with "28" inside: texture |
| Hands (about 10:09:30) | hour 305.5 deg Mercedes, minute 63.55 deg, seconds 186.4 deg with lume ring, GMT 152.9 deg: GREEN shaft (0.4 mm) with the triangular lume head (vertical right edge x 1094.5) |
| Crown / case | fluted crown on the LEFT: x 492 .. 432 flutes, cap to 406, y 1359..1517, axis 0.6 mm below the pivot; guards to x 447; lug top y 903.5, lug bottom y 1992.5 |
| Bracelet | Oyster, three columns (outer brushed, wider polished centre); column lines x about 860 / 1059.5; joints in `config/watches/rolex-gmtmaster40-126720vtnr.json` (`strap.bracelet.note`); ends y 683.2 / 684.8 (top) and 2514.4 (bottom) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_gmtmaster40_left.py` (variant copy of `watch_rolex_gmtmaster40`: crown block follows trace.crown.side) |
| Prep | `pipeline/rolex_gmtmaster40_left_prep.py <key>` (variant copy of `rolex_gmtmaster40_prep`: measure `crown_side: "left"`, `case_edge_right_x`, `crown_rows.left_x`) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_gmtmaster40.json` (read-only; pivot and scale agree within a pixel) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_gmtmaster40_left_prep 126720vtnr   # -> config/watches/rolex-gmtmaster40-126720vtnr-trace.json, outputs/watches/rolex-gmtmaster40-126720vtnr/{dial_photo,steel_photo}.jpg
```
