# Reference plan: TUDOR Black Bay Chrono M79360N-0013 (41 mm steel, black dial with two silver sub-dials, black tachymeter bezel, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Black Bay GMT ([-0001](../tudor-black-bay-gmt-m79830rb-0001/REFERENCE_PLAN.md)), Black Bay 58 and Black Bay 54 builds; the Black Bay Chrono is a different model (41 mm case, sub-dials, two angled chronograph pushers, tachymeter bezel, five-column bracelet), so this build sets the **Black Bay Chrono template**.

## Target asset

Front relief GLB `models/watches/tudor-m79360n-0013.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79360n-0013_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay GMT / 54 builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole (449, 612))

| Item | Result |
| --- | --- |
| Alpha bbox | x 168..771 (771 = crown), y 142..1122; bracelet 470 px above and 510 px below the pivot |
| Scale | bezel left edge x 169 on the pivot row: 280 px = 20.5 mm, 13.6585 px/mm (41 mm anchor) |
| Rings (r from pivot, radial profiles) | dial_flat 199 (minute track), black rehaut 200..214, polished flange 215..233, black insert 233..276 (numerals 60..500, pearls and ticks in the photo), steel outer rim to 280. Perspective: the flange outer edge is 224 px at 12 and 237 px at 6, the rings are averages |
| Hands (about 10:09) | hour = free polygon (arrow-like block 6.8 mm wide, stem 1.1 mm, tip 8.3 mm from the pivot); minute 14.05 mm at 63.6 deg, half width 0.5 mm, point from 13.0 mm; central chronograph seconds hand pointing down: ball tip r 0.5 mm at 4.5 mm, needle 0.22 mm half width, triangle tail at 12 (width 2.7 mm, apex 10.3 mm, base 12.9 mm); sub-dial hands in the map and as 3D copies |
| Sub-dials | left centre (340.9, 615) r 61 px, hub r 8.7 px, hand to the lower left; right centre (553.5, 615.5) r 61 px, hand up |
| Crown / pushers | crown fluted x 731..771, y 570..674 (r 3.81 mm, centre y -0.73 mm), neck 721..731; pushers at 2 and 4 o'clock radial from (449, 622) at +-30 deg, r 26 px, end faces 341.5 px away |
| Case | lug top edge y 300 (22.84 mm), bottom y 945 (24.38 mm) |
| Bracelet | five columns (outer / inner / centre / inner / outer), vertical joint lines top x 384 / 428 / 470 / 515, bottom 383 / 428 / 469 / 513; joints in the spec |
| Dial | black, round lume dots, bar indices, red 12 marker, TUDOR shield, GENEVE, 200 m 660 ft, CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, date window at 6 o'clock showing 28 (flat in the map) |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines measured from the photo |
| Bezel numerals, dial print, date, sub-dial scales | flat in the photo (projected / dial map), not applied geometry |
| Pushers | 3D cylinders (neck, fluted ring, cap) along the photo's axis, steel_photo texture |
| Pose | 10:09 as photographed; front-locked |
| Comparison frame | 2048 px square, 27.317 px/mm centred on the pivot (2x photo pivot (898, 1224) at (1024, 1024), offset (+126, -200)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bbchrono_prep m79360n-0013   # -> 2x reference, config/watches/tudor-bbchrono-m79360n-0013-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
