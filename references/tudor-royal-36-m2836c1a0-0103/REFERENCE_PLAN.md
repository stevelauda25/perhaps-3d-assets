# Reference plan: TUDOR Royal 36 M2836C1A0-0103 (steel, green sunburst dial, applied baton indices, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the approved -0101 build ([../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md)); only the differences are listed in full here.

## Target asset

Front relief GLB in `models/watches/tudor-m2836c1a0-0103.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background, 900 x 1200 | `tudor-m2836c1a0-0103_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights estimated (as -0101), back flat |

## Measured against -0101 (same camera, same 900 x 1200 frame)

| Item | Result |
| --- | --- |
| Silhouette (alpha), bracelet joints, polished channel pieces, crown, bezel ribs | Identical to -0101 outside the dial (mean abs RGB difference 0.3 over the area beyond r = 260 px; only the drop shadow differs). Spec values kept. |
| Hand pivot, hour / minute / seconds tips and tails, widths, hub, lume ranges | Same pose and shapes at 14 px/mm grid inspection (hour tip, minute tip, hub crops overlay to the pixel). `-0103-measure.json` is the -0101 measurement. |
| Date window | Same place (565, 647)-(614, 688); white window, black numerals, 2.5 mm frame |
| Rings (bezel_in 216, crystal_edge 213, dial_flat 207, bezel_out 248), case edge x 195, scale 14.0556 px/mm, pivot (448, 664) | Unchanged; kit preset `watch_kit_white_front_tudor_royal36.json` is reused (camera 28.1112 px/mm) |

## Differences from -0101

| Part | -0101 | -0103 |
| --- | --- | --- |
| Dial | black sunburst, gold Roman numerals | green sunburst, applied steel baton indices (one bar at each hour except 3, which is the date window), thin white minute track, TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE; all flat in the photo map |
| Hands | gold, cream lume | steel with a white lume strip; seconds needle thin steel. Built with `hands.material = steel_photo` and `hands.lume_material = steel_photo` (front-projected photo, as the case) because a plain polished-steel material rendered flat grey |
| Step file | `watch_tudor_royal36.py` | `watch_tudor_royal36_0103.py`: a copy with one added key (`hands.lume_material`); the shared step is untouched |
| Bracelet joint gap | 0.4 mm | 0.12 mm (matches the photo's thin joint lines better) |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands in the map | Left in (as -0101); the 3D hands cover them at the photographed pose |
| Indices | Flat in the map, not applied geometry; raising them needs a clean trace, offered if wanted |
| Bracelet | Flat, row joints at the photo's measured positions (same numbers as -0101) |
| Pose | 10:09 as photographed; front-locked presentation |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal36_prep 0103   # -> 2x reference, config/watches/tudor-royal36-m2836c1a0-0103-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
