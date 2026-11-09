# Reference plan: ROLEX Air-King 116900 (40 mm steel, black dial, domed polished bezel, Oyster bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo from the retailer wristcheck.com (see `sources.md`; Catalog 2 tracker position 37). FOLLOWER of the finished Air-King 126900 ([BASELINE.md](../rolex-air-king-126900/baseline/BASELINE.md)): same step and prep read-only (spec / measure driven), own measure, spec, job and kit preset.

## Target asset

Front relief GLB `models/watches/rolex-116900.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, domed bezel with window chamfer, crystal, dial plate, three hands at different heights, hub, crown, bracelet rows, centre-link pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright product render, transparent background, 2880 x 2880 RGBA PNG, soft (strongly upscaled), the watch is 1402 x 2469 px incl. the crown | `rolex-116900_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the 126900 template (back flat) |

## Measured on this photo (continuous px of the native 2880 x 2880 frame)

| Item | Result |
| --- | --- |
| Anchor | listed 40 mm = left flank of the bezel (median alpha edge over rows 1204..1324) to the pivot 20 mm: 32.6253 px/mm (126900: 22.586, so 1.444x); the crown notch (right flank) is x 2080 |
| Pivot | centre of the hub (1437.0, 1233.0); fitted from the seconds line x = 1550.39 - 0.0919 y (hand angle 185.25 deg) and the hub disc (x 1408..1470, bottom y 1263); hour / minute axes pass about 6.5 / 4.5 px off it |
| Bezel | outer ellipse centre (1437.2, 1233.7), half axes 653.0 x 635.2 (flank 9 o'clock, gradient edges y 598.5 / 1869); window edge circle centre (1436.4, 1230.1) r 553.7 (16.97 mm; std 5.8 px, soft); the black reflection on the bezel and its highlights are texture |
| Case | lug tips at y 488 (22.8 mm, spec 22.75) and y 2056 (25.2 mm, spec 25.25); no separate crown guards in the silhouette; crown barrel x 2080..2184, y 1137..1358, axis y 1247.5, radius up to 111 px |
| Dial | black dial, white 3 / 6 / 9 and minute numerals, triangle at 12, green ROLEX, Air-King script: all in the native photo map |
| Hands (10:09:30) | hour 305 deg (lume leaf head, tip s 256 px), minute 63.4 deg (baton with spear tip, s 443), seconds 185.25 deg (green, line 16 px, lume disc r 24 at s 256, tail disc r 14 at s -151, tip s 466); hub r 30 / 20 px. A different hour hand shape than 126900 (no Mercedes disc: a leaf head) |
| Bracelet | Oyster, three columns: outer-link rows (top joints 345, 283; bottom 2280, 2550) and centre links x 1294..1577 (top joints 308, 508; bottom 2018, 2090, 2326, 2381, 2572); widths follow the silhouette |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep | read-only `pipeline/steps/watch_rolex_airking.py` and `pipeline/rolex_airking_prep.py` (key 116900) |
| Comparison frame | 1536 px square at half the native scale (16.3127 px/mm) centred on the pivot (half-size photo pivot (718.5, 616.5) at (768, 768)), `config/presets/watch_kit_white_front_rolex_airking116900.json` (1280 does not hold the 44.1 mm bracelet below the pivot at this scale) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_airking_prep 116900   # -> config/watches/rolex-airking-116900-trace.json, outputs/watches/rolex-airking-116900/{dial_photo,steel_photo}.jpg
```
