# Reference plan: ROLEX Yacht-Master 42 226627 (42 mm RLX titanium, black ceramic bezel insert, black dial, date with Cyclops lens, titanium Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the finished Yacht-Master 40 template (`../rolex-yacht-master-40-126622/baseline/BASELINE.md`, section "Template for the next Yacht-Master variants"): step and kit-preset logic reused, own kit preset, variant-named prep copy (the original hard-codes the `rolex-yachtmaster40-` file prefix).

## Target asset

Front relief GLB `models/watches/rolex-226627.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, bezel band with chamfer + polished ring, toothed-edge ring, crystal, dial plate, Cyclops lens above the crystal, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1069 x 1879 px incl. the crown | `rolex-226627_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Yacht-Master 40 template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | pivot (961, 1425) (hub screw 960.6 / 1425.0, as in the YM40 render); anchor = the toothed bezel edge (tips): silhouette radius 486.6 px from the ring centre (959.5, 1425.2), left tip x 472.9 -> 42 mm -> 23.171 px/mm (the YM40 build anchored its 40 mm the same way: 460 px radius -> 23.0). The scoop gaps are opaque black in the alpha, so the outline is a circle |
| Rings (px from the ring centre) | dial flat 339, rehaut engraving 340..354, crystal edge 355, bright polished inner ring 356..380 (bezel chamfer), black ceramic band 380..465.3, polished ring 465.3..471, 60 scoops 471..486.6 (one centred at 12 o'clock) |
| Dial | black matte: round lume indices at 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11 with polished frames, a bar at 9 and 6, a triangle at 12, ROLEX coronet + wordmark, OYSTER PERPETUAL DATE, YACHT-MASTER, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut ROLEX engraving |
| Bezel | black Cerachrom insert, raised numerals 10 / 20 / 30 / 40 / 50 with black fill and polished edges, bars at 9 / 3 (black) and 1 / 11 (bright), 12 o'clock triangle (bright half, black half), minute scale 0..15, inside a polished titanium ring and a 60-scoop toothed edge |
| Hands (about 10:09:31) | hour 304.8 deg Mercedes ring (ring centre s 138, r 41), minute 63.3 deg (length 308 px), seconds 186.0 deg silver needle (tip s 325) with a tail disc (s -116, r 14) and a lollipop (s 181.5, r 25); traced outlines by the prep |
| Date window / Cyclops | rounded lens x 1108..1276.4, y 1354..1487, bright thin frame, a glass reflection, the window with the numeral inside (texture) |
| Crown / bracelet | fluted crown x 1448..1541, y 1357..1517, guards to x 1488; three-column flat Oyster bracelet, all brushed titanium (no polished centre links), joints from brightness scans (see measure) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_yachtmaster40.py` (read-only, spec driven) |
| Prep | `pipeline/rolex_yachtmaster42_prep.py <key>` (copy of the YM40 prep, only the file prefix changed) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_yachtmaster42.json` (own: pivot (961, 1425), 23.171 px/mm) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_yachtmaster42_prep 226627   # -> config/watches/rolex-yachtmaster42-226627-trace.json, outputs/watches/rolex-yachtmaster42-226627/{dial_photo,steel_photo}.jpg
```
