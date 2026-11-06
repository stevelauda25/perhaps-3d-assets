# Reference plan: TUDOR Royal 36 M2836C1A0-0102 (steel, blue sunburst dial, baton indices, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Same recipe as [-0101](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md); only the differences are listed in full. Photo and SKU from catalog 2 (see `sources.md`).

## Target asset

Front relief GLB in `models/watches/tudor-m2836c1a0-0102.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat bracelet at the photo's joints.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background, 900 x 1200 | `tudor-m2836c1a0-0102_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights estimated, back flat |

## Scale anchors

36 mm case diameter (model name), 14.0556 px/mm from the silhouette, pivot (448, 664): identical to -0101 (the alpha silhouette differs by at most 45/255 on 400 px, the steel area by 2.4 RGB levels on average), so trace, bracelet joints, polished pieces, bezel (48 segments), crown and the white kit camera (28.1112 px/mm) are reused unchanged.

## What differs from -0101

| Part | -0102 |
| --- | --- |
| Dial | Blue sunburst; applied steel baton indices, TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, white minute track dots/dashes, date at 3: all flat in the 2x photo map |
| Hands | Steel batons with a lume strip (same pose, outline and lengths as -0101, 10:09:xx). Material `steel_photo`: the 3D hands carry the photographed hand pixels projected from the front, the lume strip is part of those pixels, so the raised lume prism is a 0.04 mm sliver (it would otherwise read as a flat grey box against the photo) |
| Dial look | `dial.specular` 0.0 (0.15 on -0101 lifted the dark blue towards grey); emission 0.45 unchanged |

## Decisions

Hands, indices and print stay in the photo map (nothing invented); pose 10:09 as photographed; front-locked presentation; steel emission 0.4 as -0101.

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal36_prep 0102   # -> 2x reference, config/watches/tudor-royal36-m2836c1a0-0102-trace.json, dial and steel maps
```
