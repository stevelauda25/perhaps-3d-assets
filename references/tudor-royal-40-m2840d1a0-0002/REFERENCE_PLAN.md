# Reference plan: TUDOR Royal 40 M2840D1A0-0002 (steel, blue sunburst dial, Roman numerals, day-date, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe and Royal 40 template as [-0001](../tudor-royal-40-m2840d1a0-0001/REFERENCE_PLAN.md); dial behaviour and numeral layout follow the Royal 36 Roman builds ([-0101](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md) black, -0104 silver, -0105 salmon).

## Target asset

Front relief GLB `models/watches/tudor-m2840d1a0-0002.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m2840d1a0-0002_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from -0001, back flat |

## Checked on this photo against the -0001 template

Alpha silhouette differs from -0001 by at most 49/255 in 72 px; steel pixels outside the dial (r > 280 px) differ by 0.8/255 on average, so the camera template is shared. Pivot (450, 609), case left edge x 172, 13.9 px/mm, rings, crown box, bracelet joints and hand tip/tail positions are the -0001 values (hands read on the gridded crop: hour tip about (353, 543), minute tip about (623, 518), 10:09). Date window at x 582..620, y 590..625 (same box, "28"); MONDAY window at 12.

## Per-dial differences

| Item | -0002 |
| --- | --- |
| Dial | blue sunburst, silvered Roman numerals around the dial (none at 12: MONDAY window; the minute hand lies over the numeral near 2 as in the photo; a partial numeral stub beside the date window at 3), TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, blue/silver minute track; all flat in the dial map |
| Hands | steel/silver batons with white lume strips and a steel seconds hand; they carry the steel photo map, no colour parameter |
| Dial emission | 0.33 (0.40 read 4.2% light, 0.37 read 3.0%, 0.33 reads 1.3%; the response is nonlinear) |

## Decisions

Same as -0001: hands left in the map and covered by 3D hands carrying the projected photo; numerals, windows flat in the map; flat bracelet at the measured joints; pose 10:09; comparison frame 2048 px, 27.8 px/mm centred on the pivot.

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0002   # -> 2x reference, config/watches/tudor-royal40-m2840d1a0-0002-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
