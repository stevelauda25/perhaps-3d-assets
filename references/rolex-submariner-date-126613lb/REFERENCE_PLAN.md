# Reference plan: ROLEX Submariner Date 126613LB (41 mm steel and yellow-gold Rolesor, blue dial, blue Cerachrom bezel with gold coin edge, date with Cyclops lens, two-tone Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Submariner Date 41 template built for the 126610LN (`../rolex-submariner-date-126610ln/baseline/BASELINE.md`).

## Target asset

Front relief GLB `models/watches/rolex-126613lb.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, Cyclops lens above the crystal, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1028 x 1855 px incl. the crown | `rolex-126613lb_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | same camera as the 126610LN / 124060 (alpha masks equal except the bracelet end rows and 5 px of the crown cap); scale 22.785 px/mm, pivot (960, 1424); lens polygon, rings, crown and bracelet joints re-checked by overlay on 5-10x crops |
| Dial | blue sunburst Maxi dial (dark blue rim, lighter blue upper right): white round indices with gold rims at 1 / 2 / 4 / 5 / 7 / 8, bar at 9, long bar at 6, triangle at 12, ROLEX coronet, OYSTER PERPETUAL DATE, SUBMARINER 1000ft = 300m, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut engraving, date window with Cyclops at 3 showing 28 |
| Hands (about 10:09:30) | hour 305.5 deg, minute 63.55 deg, seconds 186.3 deg (same as the template). Unlike the black-dial template the hands are GOLD with white lume and dark facets on a blue dial, so the grey threshold trace cannot be used: hour and minute outlines are re-measured polygons (measure `hands.*.mode = shapes`: hour stem + arrow polygon + two circles for the Mercedes ring and its lower-left facet, minute polygon with parallel edges w -15.5 / +15.5 px to s 228, tip at s 287.6), the seconds needle uses the template polygon (gold needle centre line x = 968.5 - 0.1077 (y - 1340), i.e. 186.1 deg) |
| Bezel / case / crown / bracelet | blue ceramic insert with gold numerals / markers, YELLOW-GOLD fluted coin edge (all from the projected photo), gold crown with steel guards, two-tone Oyster bracelet (steel outer links, gold centre links, same joint rows as the template) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep | `pipeline/steps/watch_rolex_submarinerdate41.py` and `pipeline/rolex_submarinerdate41_prep.py 126613lb`, read-only |
| Kit preset | `config/presets/watch_kit_white_front_rolex_submariner41.json`, read-only |
| Gold parts | no separate material: gold coin edge, crown and centre links carry the projected photo like the steel; the shared steel / bezel emission is re-tuned per region (see BASELINE) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_submarinerdate41_prep 126613lb   # -> config/watches/rolex-submarinerdate41-126613lb-trace.json, outputs/watches/rolex-submarinerdate41-126613lb/{dial_photo,steel_photo}.jpg
```
