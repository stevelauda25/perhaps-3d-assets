# Reference plan: TUDOR Royal 40 M2840D1A0-0003 (steel, green sunburst dial, applied Roman numerals, day-date, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Built with the Royal 40 template set by [-0001](../tudor-royal-40-m2840d1a0-0001/REFERENCE_PLAN.md) (measure values, spec, step, kit preset reused read-only); dial colour and numeral handling follow the Royal 36 Roman builds ([-0101](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md) black, -0104 silver, -0105 salmon).

## Target asset

Front relief GLB `models/watches/tudor-m2840d1a0-0003.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m2840d1a0-0003_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from -0001, back flat |

## Checked against -0001 (same photo template)

| Item | Result |
| --- | --- |
| Alpha silhouette | identical to -0001 (0 px differ by more than 128/255), bbox x 171..763, y 121..1115; bracelet pixel diff to -0001 under 0.4 grey levels |
| Pivot, scale | (450, 609), 13.9 px/mm (40 mm anchor), as -0001 |
| Hands (10:09) | same lengths, angles and tails as -0001 on a side-by-side crop; the hands here are steel (silver) with lume strips, not gold |
| Date window | same box as -0001 (581..621, 589..628); day window MONDAY at 12 |
| Dial | green sunburst, silver applied Roman numerals (XII hidden by the MONDAY window, III by the date window, II partly hidden by the minute hand as in the photo), TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, minute track; all flat in the 2x photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`steel_photo`) as in -0001 |
| Numerals, windows | flat in the map, not applied geometry |
| Bracelet | flat, row joints and polished pieces at the -0001 positions |
| Dial emission | per dial, tuned against the photo (see BASELINE.md) |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, 27.8 px/mm, pivot at the frame centre (same kit as -0001) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0003   # -> 2x reference, config/watches/tudor-royal40-m2840d1a0-0003-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
