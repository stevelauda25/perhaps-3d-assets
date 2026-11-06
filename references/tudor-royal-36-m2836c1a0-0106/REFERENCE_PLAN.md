# Reference plan: TUDOR Royal 36 M2836C1A0-0106 (steel, light blue sunburst dial, blue baton indices, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe and template as [-0101](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md); closest siblings -0102/-0103 (baton indices) and -0104 (light dial).

## Target asset

Front relief GLB `models/watches/tudor-m2836c1a0-0106.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat bracelet with rows at the photo's joints.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background, 900 x 1200 | `tudor-m2836c1a0-0106_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights estimated, back flat |

## Scale anchors

36 mm case diameter (model name; 14.056 px/mm from the silhouette left of the pivot). Pivot (448, 664) px, identical to the other Royal 36 photos. Heights estimated, house depth scale 0.35.

## Part by part (differences from -0101 only)

| Part | Note |
| --- | --- |
| Case, bezel, crown, bracelet | Same template: alpha silhouette differs from -0103 by at most 48/255, steel-region mean RGB difference 0.8 |
| Dial | Light blue sunburst; applied blue (dark-outlined) baton indices, TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, date at 3 with white window; no Roman numerals. Photo map, flat. |
| Hands | Blue batons with dark blue outline and white lume strip, blue seconds needle; 10:09 pose as the others. Photographed pixels carried by the 3D hands (steel_photo) and left in the dial map. |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal36_prep 0106
```
