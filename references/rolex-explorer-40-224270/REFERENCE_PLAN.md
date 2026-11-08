# Reference plan: ROLEX Explorer 40 224270 (40 mm steel, black dial, smooth domed polished bezel, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from the Rolex image host (see `sources.md`; Catalog 2 tracker position 45). ADAPT of the finished Rolex Air-King 126900 build (same 40 mm Oyster family, same bezel type, same camera): the Air-King step `pipeline/steps/watch_rolex_airking.py` is reused read-only, the prep is a variant-named copy (`pipeline/rolex_explorer40_prep.py`, only file names differ). A sibling builds the Submariner 124060 at the same time from its own files.

## Target asset

Front relief GLB `models/watches/rolex-224270.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, domed bezel with window chamfer, crystal, dial plate, three hands at different heights, hub, crown, bracelet rows, centre-link pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 965 x 1831 px incl. the crown | `rolex-224270_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Air-King template (back flat) |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | listed 40 mm = left flank of the bezel (median alpha edge over rows 1400..1470, x 514.2) to the pivot 20 mm: 22.2453 px/mm (the Air-King render measures 22.586 on the same 40 mm; the bracelet is the same width in both photos, so the Explorer bezel is 1.5 % smaller on screen); the silhouette is symmetric about x 960.0 |
| Pivot | centre of the hub (959.2, 1425.0), screw at (960.5, 1424.5) |
| Bezel | smooth domed polished, outer ellipse centre (960.0, 1427.5) half axes 445.9 x 442.0 (left silhouette, radial edges at 12 / 6 o'clock); inner edge (outer edge of the dark bevel line around the rehaut) a circle centre (955.0, 1418.8) r 385.2 (left 568.7, right 1340.5, top 1034.7, bottom 1802.0: the window sits 5 px left of the pivot) |
| Case | no crown guards in the silhouette; lugs top end at the outer-link joint y 920 (22.7 mm), bottom end y 1984 (25.1 mm); crown barrel x 1402..1450, rows 1357..1513 (axis y 1435, radius 78 px), domed cap to x 1478 |
| Dial | black dial, applied white-framed Arabic 3 / 6 / 9, white triangle at 12, baton indices, ROLEX with crown, OYSTER PERPETUAL, EXPLORER, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE; minute track and rehaut ring: all in the native photo map |
| Hands (10:09:30) | hour 304.6 deg (Mercedes disc r 37.5 at s 117, arrowhead tip s 200.7), minute 63.1 deg (sword, tip s 318.5), seconds 186.1 deg (line half width 3.2, tail disc r 13.7 at s -108.5, lume head disc r 21.2 at s 182.7, tip s 331); hub r 26 / 19.5 px |
| Bracelet | Oyster, three columns: brushed outer-link rows (top: joints 762.5, 920; bottom: 1984 (lug end), 2175.5, 2352.5, 2481, end 2514) and centre links x 858..1062 (top joints 728.5, 864.5; bottom 2056, 2233.5, 2395.5, 2497) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_airking.py`, read-only (spec driven) |
| Prep | `pipeline/rolex_explorer40_prep.py` (variant-named copy of `rolex_airking_prep.py`) |
| Comparison frame | 1280 px square at half the native scale (11.1227 px/mm) centred on the pivot (half-size photo pivot (479.6, 712.5) at (640, 640)), `config/presets/watch_kit_white_front_rolex_explorer40.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_explorer40_prep 224270   # -> config/watches/rolex-explorer40-224270-trace.json, outputs/watches/rolex-explorer40-224270/{dial_photo,steel_photo}.jpg
```
