# Reference plan: PATEK PHILIPPE Aquanaut 5168G blue (42.2 mm white gold, blue embossed dial, blue composite rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 104 (see `sources.md`). Follower of the [5168G green](../patek-aquanaut-5168g-green/REFERENCE_PLAN.md) build, itself a follower of the [5167A-001](../patek-aquanaut-5167a-001/REFERENCE_PLAN.md) Aquanaut template.

## Target asset

Front relief GLB `models/watches/patek-5168g-blue.glb` (tracker rule: lowercase brand + normalized SKU, variant appended because the SKU repeats), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2691 RGBA PNG, the watch is 1365 x 2162 px incl. the crown | `patek-5168g-blue_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights are the template's, back flat |

## Measured on this photo (continuous px of the native frame; details in `config/watches/patek-aquanaut42-5168g-blue-measure.json`)

The blue photo is the same render family as the green one but not the same pose: 0.4 % smaller (29.719 px/mm), hub 20 px higher in the frame, and parts at different heights shifted against each other (lug tips 24.25 mm above / 26.5 mm below the hub, crown axis 15 px below the hub, strap ends at 31.5 / 40.7 mm, hand centre lines 3.7 px left (hour) and 2.6 px right (minute) of the hub), so nothing is copied from the green in pixels; only the mm-based shapes (hand profiles, crown profile scaled, heights, materials) are the template's.

| Item | Result |
| --- | --- |
| Anchor | left flank of the case 332.49 px = 21.1 mm from the pivot (959.56, 1334.86) |
| Bezel | superellipse centre y 1338.25, half axes 627.07 x 620.75 px, exponent 2.25, cut back to the silhouette; window scanned on 720 rays |
| Dial | midnight-blue graded embossed "globe grid" dial, applied numerals and indices, native photo map |
| Hands | hour 303.58 deg, minute 51.08 deg, seconds 179.51 deg; pale grey lume inlays |
| Crown | rows 1267..1434, axis y 1350.5, tip x 1696.6 |
| Strap | navy composite rubber, straight inner walls (top 632 -> 623 / 1299 -> 1293, bottom 630 -> 637.5 / 1300 -> 1292.5) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_aquanaut42_blue_prep 5168g-blue 5168g-blue   # -> config/watches/patek-aquanaut42-5168g-blue-trace.json, outputs/watches/patek-aquanaut42-5168g-blue/{dial_photo,steel_photo}.jpg
```
