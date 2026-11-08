# Reference plan: ROLEX Sea-Dweller Deepsea 136660 D-Blue (44 mm steel, gradient dial, black Cerachrom bezel with coin edge, date without Cyclops, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER / ADAPT of the Sea-Dweller 43 template (`../rolex-sea-dweller-126600/baseline/BASELINE.md`, itself an adapt of the Submariner Date 41 template): same step (spec driven), prep copy renamed only for the `rolex-deepsea44-` file prefix, everything re-measured on this photo.

## Target asset

Front relief GLB `models/watches/rolex-136660.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing). No Cyclops lens, no helium valve mesh.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1103 x 1925 px incl. the crown | `rolex-136660_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up / helium valve | none | not available; heights follow the Sea-Dweller template, back flat. The valve is on the 9 o'clock flank and not visible in this render |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | scale 22.591 px/mm (44 mm = coin-edge tip diameter = 2 x (960.0 - 463.0) px, left tip envelope near the pivot row; cross-check: crown diameter 181 px = 4.0 mm radius, bracelet 22 mm nominal at the lugs ~ 497 px), pivot = hub screw (960, 1422), ring centre (959.5, 1420.0) (insert / dial fits 1417.9..1424.2) |
| Dial | gradient dial (blue at the top to black at the bottom): triangle at 12, round indices 1 / 2 / 4 / 5 / 7 / 8 (no index at 3: date window), bar at 9, long bar at 6, ROLEX coronet, OYSTER PERPETUAL DATE, DEEPSEA in green, 12800ft = 3900m, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, rehaut engraving ORIGINAL GAS ESCAPE VALVE / RING LOCK SYSTEM |
| Date | white window with the 28 at 3 o'clock, flat (no Cyclops): texture in the dial map |
| Hands (about 10:09:30) | hour 305.5 deg Mercedes, minute 63.1 deg, seconds 185.55 deg with tail dot and lume ring; traced outlines by the prep |
| Bezel | black ceramic insert (r 365.9..461.1 px) with a baked white reflection, polished rim to r 468.4, coin edge 60 flutes (ridge at 3.05 deg mod 6 deg, ripple 1.4 px) to the tips at r 496.5 |
| Case / crown / bracelet | lug tops slope 877 -> 863, bottoms 2021 -> 2035; crown guards plateau x 1515 (rows 1280..1346 and 1528..1592), crown x 1460..1565, rows 1346..1527; three-column Oyster bracelet (joint rows in `config/watches/rolex-deepsea44-136660-measure.json`) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_seadweller43.py` used read-only (spec driven; the spec has no `date` section) |
| Prep | `pipeline/rolex_deepsea44_prep.py <key>` (copy of `rolex_seadweller43_prep.py`, only the name prefix differs) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_deepsea44.json` (22.5909 / 2 px/mm, pivot (960, 1422) at the frame centre) |
| Helium valve | no mesh: nothing in the silhouette, hidden behind the bezel |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_deepsea44_prep 136660   # -> config/watches/rolex-deepsea44-136660-trace.json, outputs/watches/rolex-deepsea44-136660/{dial_photo,steel_photo}.jpg
```
