# Reference plan: TUDOR Royal 40 M2840D1A0-0004 (steel, silver sunburst dial, applied gold baton indices, day-date, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe and Royal 40 template as [-0001](../tudor-royal-40-m2840d1a0-0001/REFERENCE_PLAN.md); only the dial differs.

## Target asset

Front relief GLB `models/watches/tudor-m2840d1a0-0004.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m2840d1a0-0004_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Royal 40 -0001 build, back flat |

## Checked on this photo against the -0001 template

| Item | Result |
| --- | --- |
| Silhouette | alpha differs from -0001 by at most 44/255 in 48 px; steel pixels outside the dial differ by 0.6/255 on average: pivot (450, 609), scale 13.9 px/mm, rings, crown, bracelet joints, bezel phase all hold |
| Hands (10:09:xx) | gold batons with white lume strips on hour and minute, thin gold seconds with tail: same place and length as -0001 |
| Dial | silver sunburst, applied gold baton indices (none at 3: date window; none at 12: MONDAY window), TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, black minute track; no Roman numerals (confirmed on the photo); all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands, indices, windows | as -0001: hands left in the map and covered by 3D hands carrying the front-projected photo; indices and windows flat in the map |
| Bracelet | flat, row joints and polished pieces at the -0001 template positions |
| Dial emission | silver dial: checked both ways (see BASELINE.md); the response is nonlinear |
| Comparison frame | 2048 px square, shared Royal 40 kit preset (27.8 px/mm, pivot at the centre) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0004   # -> 2x reference, config/watches/tudor-royal40-m2840d1a0-0004-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
