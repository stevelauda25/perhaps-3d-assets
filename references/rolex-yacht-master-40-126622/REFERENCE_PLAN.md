# Reference plan: ROLEX Yacht-Master 40 126622 (40 mm steel / platinum, slate dial, date with Cyclops lens, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL (Yacht-Master) adapting the finished Submariner Date 41 template (`../rolex-submariner-date-126610ln/baseline/BASELINE.md`: bezel rings, coin edge, Cyclops lens) and the Explorer 40 build; this is the Yacht-Master 40 template (the Yacht-Master 42 226627 follows).

## Target asset

Front relief GLB `models/watches/rolex-126622.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, platinum bezel band + polished ring, toothed-edge ring, crystal, dial plate, Cyclops lens above the crystal, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1030 x 1836 px incl. the crown | `rolex-126622_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Submariner Date template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | pivot (961, 1425) (hub screw 960.8 / 1425.0); the toothed bezel edge (scoop tips) has radius 460 px = 20.0 mm -> 23.0 px/mm (anchor: the 40 mm case); ring centre (959.6, 1424.5); rings 310 / 351 / 352.6 / 430 / 437 / 460 px (dial flat, crystal edge, bezel inner edge, matte band outer, polished ring outer, tooth tips); the case flank beside the bezel (x 484) is the lug body (20.7 mm radius at this scale). The render is a slightly tilted (about 6 deg) view: lower parts shift down (bezel inner edge centre y 1424.3, toothed edge ~1427, flank 1437), a 0.5 % vertical squeeze |
| Dial | slate / rhodium sunburst: round lume indices at 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11, a long bar at 6 and a horizontal bar at 9, a triangle at 12, no index at 3 (date window), ROLEX coronet + wordmark, OYSTER PERPETUAL DATE, YACHT-MASTER in cyan, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut ROLEX engraving |
| Bezel | platinum, matte: raised polished numerals 10 / 20 / 30 / 40 / 50 (the 10 / 20 / 40 / 50 have black fill in the engraving), black bars at 9 / 3, a triangle with a black half at 12, minute scale 0..15 with black graduations, polished ring, 60 scoops (one centred at 12) |
| Hands (about 10:09:31) | hour 304.8 deg Mercedes ring (ring centre s 113), minute 63.3 deg with lume strip, seconds 186.0 deg cyan needle with a tail disc (s -103) and a lollipop (s 161, white lume inside); traced outlines by the prep |
| Date window / Cyclops | rounded lens x 1088.6..1253, y 1356.4..1488 (7.2 x 5.7 mm), bright thin frame, a glass reflection arc, the window with the numeral inside (texture) |
| Crown / bracelet | fluted crown x 1425..1513, y 1357..1513, guards to x 1466; three-column flat Oyster bracelet, brushed outer links, polished centre links, joints from brightness scans (see measure) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_yachtmaster40.py` (copy of the Submariner Date 41 step; platinum bezel, scoop phase / power; the Yacht-Master 42 reuses it read-only) |
| Prep | `pipeline/rolex_yachtmaster40_prep.py <key>` (copy of the Submariner Date 41 prep) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_yachtmaster40.json` (own: pivot (961, 1425), 23.0 px/mm) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_yachtmaster40_prep 126622   # -> config/watches/rolex-yachtmaster40-126622-trace.json, outputs/watches/rolex-yachtmaster40-126622/{dial_photo,steel_photo}.jpg
```
