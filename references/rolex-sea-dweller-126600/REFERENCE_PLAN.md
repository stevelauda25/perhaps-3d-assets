# Reference plan: ROLEX Sea-Dweller 126600 (43 mm steel, black dial, black Cerachrom bezel with coin edge, date with Cyclops lens, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). ADAPT of the Submariner Date 41 template (`../rolex-submariner-date-126610ln/baseline/BASELINE.md`, itself a follower of the no-date Submariner 124060): same step / prep family, re-measured on this photo; this is the Sea-Dweller 43 template (the Deepsea 136660 D-Blue follows).

## Target asset

Front relief GLB `models/watches/rolex-126600.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and thick crown guards, ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, Cyclops lens above the crystal, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1080 x 1900 px incl. the crown | `rolex-126600_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up / helium valve | none | not available; heights follow the Submariner template, back flat. The valve is on the 9 o'clock flank and not visible in this render |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | scale 23.0 px/mm (43 mm = coin-edge tip diameter = 2 x (959.6 - 465.1) px; cross-check: bracelet at the lugs 489 px = 21.3 mm, nominal 21), pivot = hub screw (960, 1423), ring centres 1.3..4.5 px above the pivot (the camera sees the taller case at a slight angle: dial edge centre y 1426, flange 1421.2, insert 1421.9) |
| Dial | black Maxi dial: Mercedes-ring hour hand, round indices 1 / 2 / 4 / 5 / 7 / 8, NO index at 3 (date window), bar at 9, long bar at 6, triangle at 12, ROLEX coronet, OYSTER PERPETUAL DATE, SEA-DWELLER in red, 4000ft = 1220m, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut ROLEX engraving |
| Date window / Cyclops | lens with flat top (y 1351) and bottom (y 1483), bowed sides, x 1087.5..1255.5 (7.3 x 5.7 mm, centre 9.3 mm right of the pivot); bright thin frame, a glass reflection arc; the white date window with the numeral inside (texture) |
| Hands (about 10:09:30) | hour 305.5 deg Mercedes, minute 63.55 deg, seconds 186.3 deg with tail dot and lume ring; traced outlines by the prep |
| Bezel | black ceramic insert (r 367.3..460.5 px), polished rim to r 466.8, coin edge with 60 flutes (pitch 6.0 deg, silhouette ripple about 1 px) to the tips at r 494.5 |
| Case / crown / bracelet | case 43 mm with thick crown guards (silhouette plateau x 1499 over rows 1288..1344 and 1528..1590), fluted crown x 1452..1544, three-column Oyster bracelet with Glidelock end (joint rows in `config/watches/rolex-seadweller43-126600-measure.json`); no helium valve in the silhouette |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_seadweller43.py` (copy of the Submariner Date 41 step + `bezel.flute_phase_deg`); the Deepsea reuses it read-only |
| Prep | `pipeline/rolex_seadweller43_prep.py <key>` (copy of the Submariner Date 41 prep, own name prefix) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_seadweller43.json` (23.0 / 2 px/mm, pivot (960, 1423) at the frame centre) |
| Helium valve | no mesh: hidden behind the bezel in the front render, nothing in the silhouette |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_seadweller43_prep 126600   # -> config/watches/rolex-seadweller43-126600-trace.json, outputs/watches/rolex-seadweller43-126600/{dial_photo,steel_photo}.jpg
```
