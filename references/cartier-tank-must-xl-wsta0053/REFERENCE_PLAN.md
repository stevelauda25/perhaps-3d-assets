# Reference plan: CARTIER Tank Must Extra-Large Automatic WSTA0053 (41 x 31 mm steel, silver dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same projected-photo recipe as the Tudor builds ([Black Bay 54](../tudor-black-bay-54-m79000n-0001/REFERENCE_PLAN.md)), adapted for a rectangular case and a photo without alpha. This is the first Cartier: it also sets the **Cartier approach** (mask from the JPEG, rectangular case, crown, hands, dial) that the Santos de Cartier WSSA0018 reuses.

## Target asset

Front relief GLB `models/watches/cartier-wsta0053.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, light background with soft shadow gradient, 750 x 750 JPEG without alpha | `cartier-wsta0053_original.jpg` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness about 6.6 mm), back flat |

## Measured on this photo (px of the 750 x 750 frame, pivot = hub centre (367.5, 368.5))

| Item | Result |
| --- | --- |
| Silhouette | derived mask (see `sources.md`): bbox x 237..536 (536 = crown), y 81..660; the bracelet runs 295 px (34.1 mm) above and 292 px (34.5 mm) below the pivot |
| Scale | case width 31 mm = 262 px between the brancard outer edges (rows 260..340) gives 8.4516 px/mm; the lug-to-lug height (brancard top 197.5 to bottom 543.5 = 346 px) then reads 40.9 mm against the listed 41 mm (checked in the step, not used) |
| Case | Tank brancards: two rounded vertical bars, outer 237.5 / 498.5, inner edge 268 / 468 (3.6 mm wide), corner radius about 3.5 mm top and bottom; brushed bars between them above the dial (y 230..250) and below (y 503..523); dial opening x 268..468, y 250..503 (23.7 x 29.9 mm); the pivot sits 118.5 px below the opening top and 134.5 px above its bottom |
| Dial | silver, circular guilloche centre with a railroad chapter rectangle (x 318..418, y 302..433), black Roman numerals (XII, I, X, XI, II, ..., VI), CARTIER, AUTOMATIC, SWISS MADE, date window at 6 (about x 357..380, y 443..470); all flat in the photo map |
| Hands (about 10:09:xx) | blue steel: hour 6.98 mm at 304.5 deg (about 0.5 mm wide), minute 10.06 mm at 55.6 deg (about 0.4 mm), seconds 9.82 mm at 219.4 deg (about 0.2 mm) with a 3.3 mm counterweight tail at 38.9 deg; blue hub radius 1.27 mm |
| Crown | steel faceted part x 498..520 (widest 52 px at x 510, five studs) plus a blue sapphire cabochon x 518..536 (radius about 1.6 mm), centre y 371 (0.3 mm below the pivot row) |
| Bracelet | three brushed columns; outer columns top pieces y 80 / 89.5 / 113.5 / 183.5 / 214.2 / 229.5 and bottom 523.5 / 548 / 556 / 612 / 650 / 664; centre column top 80 / 94 / 135 / 160 / 215.5 / 229.5, bottom 523.5 / 574.5 / 598 / 628 / 645 / 664; the vertical joints sit at x 305 / 429 at the ends and 302 / 433 at the case |

## Decisions

| Decision | Answer |
| --- | --- |
| Silhouette | mask derived from the JPEG (no alpha), recorded in `sources.md` and the trace |
| Hands | left in the dial map; 3D hands carry the front-projected photo (`hands_photo`) with outlines measured from the photo (spec `hands.profile`) |
| Numerals, guilloche, date window, print | flat in the dial map, not applied geometry |
| Crown | lathe from the measured profile with the sapphire dome; studs and blue come from the projected photo |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 1600 px square, camera 16.903 px/mm centred on the pivot (2x photo pivot (736, 738) at (800, 800), offset (+64, +62)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.cartier_tankmustxl_prep wsta0053   # -> 2x reference, mask, config/watches/cartier-tankmustxl-wsta0053-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
