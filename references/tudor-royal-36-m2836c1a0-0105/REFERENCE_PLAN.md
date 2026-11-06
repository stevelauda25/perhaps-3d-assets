# Reference plan: TUDOR Royal 36 M2836C1A0-0105 (steel, salmon sunburst dial, steel Roman numerals, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the approved -0101 build ([../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md)) with the -0103 tuning; only the differences are listed.

## Target asset

Front relief GLB in `models/watches/tudor-m2836c1a0-0105.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background, 900 x 1200 | `tudor-m2836c1a0-0105_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights estimated (as -0101), back flat |

## Measured against -0101 (same camera, same 900 x 1200 frame)

| Item | Result |
| --- | --- |
| Silhouette (alpha) | Case edge x 195, crown right edge x 740 on the pivot row; max alpha difference to -0101 is 58/255 (soft drop-shadow edge), 0 pixels above 100. Template kept. |
| Hand pivot, hour / minute / seconds tips and tails, hub | Same pose (10:09) and shapes: the -0101 measurement points land on the 0105 hand ends and hub in a 4x grid overlay. `-0105-measure.json` carries the -0101 values. |
| Date window, rings, crown, bracelet joints and polished pieces | Same positions; kit preset `watch_kit_white_front_tudor_royal36.json` reused (pivot (448, 664), 28.1112 px/mm) |

## Differences from -0101

| Part | -0101 | -0105 |
| --- | --- | --- |
| Dial | black sunburst, gold Roman numerals | salmon sunburst, steel Roman numerals, black print, thin black minute track; all flat in the photo map |
| Hands | gold, cream lume | steel with white lume strip; seconds needle thin steel. `hands.material` and `lume_material` = `steel_photo` (as -0103) |
| Step file | `watch_tudor_royal36.py` | the -0103 step copy `watch_tudor_royal36_0103.py` is used read-only (it only adds `hands.lume_material`) |
| Spec | -0101 values | -0103 tuned values: bracelet gap 0.12, steel emission 0.33, dial emission 0.4, dial specular 0 |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands in the map | Left in; the 3D hands cover them at the photographed pose |
| Numerals | Flat in the map (as -0101); the minute hand hides the II numeral as in the photo |
| Pose | 10:09 as photographed; front-locked presentation |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal36_prep 0105   # -> 2x reference, config/watches/tudor-royal36-m2836c1a0-0105-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
