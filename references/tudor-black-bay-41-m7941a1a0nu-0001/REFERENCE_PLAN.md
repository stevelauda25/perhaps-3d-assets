# Reference plan: TUDOR Black Bay 41 M7941A1A0NU-0001 (41 mm steel, black dial, black coin-edge bezel, riveted steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal, Ranger, Black Bay 54 / 58 / GMT builds; the Black Bay 41 mixes two siblings: the bezel, dial layout and hands of the [Black Bay 58 -0001](../tudor-black-bay-58-m7939a1a0nu-0001/REFERENCE_PLAN.md) (coin-edge ring around a black insert, snowflake hour hand, no crown guards, same hand artwork in px) with the three-column riveted bracelet of the [Black Bay GMT -0001](../tudor-black-bay-gmt-m79830rb-0001/REFERENCE_PLAN.md) (41 mm). So its step `pipeline/steps/watch_tudor_bb41.py` is a copy of `watch_tudor_bb58.py` with `strap.bracelet.columns = [outer, centre, outer]`. This build sets the **Black Bay 41 template** (no later variants queued).

## Target asset

Front relief GLB `models/watches/tudor-m7941a1a0nu-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow and a corner logo, 900 x 1200 | `tudor-m7941a1a0nu-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay 54 / 58 / GMT builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Alpha | watch = largest component, bbox x 168..775 (775 = crown), y 118..1123; the logo and tick marks are separate components |
| Pivot, scale | hub pin hole (451, 610) (centroid of the dark hole). Dial edge (r 203.56) and rehaut edge (r 221.25) circle fits are centred at (450.7, 610.3), within 0.4 px of the hole (`ring_centre_mm` -0.03 / -0.02). Anchor `case_edge_left_x` 169.6 (between the coin teeth tips, alpha reaches x 168, and the mean tooth edge 170.4; keeps the silhouette diameter within 0.35 mm of 41) gives 13.727 px/mm (41 mm = 2 x (451 - 169.6) px); radial scans give the coin edge at r 279.5-281 px |
| Rings (r px about the pivot) | black dial and minute track to 203.5, grey rehaut ring 204..221.3, bezel_in 222, black insert 222..269.5 (numerals 10..50, bar markers, triangle with a pearl at 12 in the photo), steel coin-edge ring 269.5..280.5 |
| Hands (10:10:38) | same artwork in px as the Black Bay 58: hour nub end at 121.2 px (8.83 mm) at 303.9 deg, stem half width 10.5-10.8 px, snowflake diamond +-32 px at 84 px; minute 180 px (13.11 mm) at 63.8 deg; seconds 182 px (13.26 mm, needle ends at the minute track) at 228.4 deg, counterweight disc r 7 at 68 px behind the hub, lume disc r 12 at 103 px; steel-white with white lume (no gold); hub radius 19 px (1.38 mm) |
| Crown | x 727..775, y 556..658 (radius 3.72 mm, centre 0.22 mm above the pivot row), 24 flutes to x 768 then a rounded cap; no crown guards |
| Case | lugs rise slightly above the round bezel: lug tops y 287 (23.53 mm), lug bottoms y 934.5 (23.64 mm) |
| Bracelet | three columns (outer / centre / outer) with rivet ears at the sides. Vertical joint lines x 387.0 / 514.5 (top), 386.3 / 514.2 (bottom). Outer joints top y 162.5 (end 118), bottom 1049 (end 1123); centre top 253 / 131.5, bottom 974 / 1080.5 |
| Dial | black glossy, silver-white luminous dots 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11, bar indices 3 / 9 / 6, triangle 12, TUDOR shield, GENEVE, 200m:660ft, MASTER CHRONOMETER, SWISS MADE; no date window; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines and lume polygons (Black Bay 58 profiles scaled to this photo's px/mm) |
| Bezel numerals, markers, dial print | flat in the photo (projected / dial map), not applied geometry |
| Bracelet | `strap.bracelet.columns` / `bounds_x_mm` / `pieces_mm` in the spec |
| Pose | 10:10:38 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, camera 27.454 px/mm centred on the pivot (2x photo pivot (902, 1220) at (1024, 1024), offset (+122, -196)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bb41_prep m7941a1a0nu-0001   # -> 2x reference, config/watches/tudor-bb41-m7941a1a0nu-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
