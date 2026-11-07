# Reference plan: TUDOR Black Bay 58 M7939A1A0NU-0001 (39 mm steel, black dial, five-link steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal, Ranger and Black Bay 54 builds ([Black Bay 54 -0001](../tudor-black-bay-54-m79000n-0001/REFERENCE_PLAN.md)); the Black Bay 58 is a different model (39 mm case, dive bezel with black insert and coin edge, snowflake hands, no crown guards, five-column jubilee-style bracelet), so this build also sets the **Black Bay 58 template** for the burgundy M7939A1A0RU-0001.

## Target asset

Front relief GLB `models/watches/tudor-m7939a1a0nu-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow and a corner logo, 900 x 1200 | `tudor-m7939a1a0nu-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay 54 build, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Alpha | watch = largest component, bbox x 180..754 (754 = crown), y 141..1123; the logo (x 629..856, y 922..1115) and tick marks are separate components |
| Pivot, scale | hub pin hole (451, 613); the dial / bezel circle is centred at about (450.2, 615.0), 2 px below the hole (not corrected: all steel parts show the projected photo). Coin-edge bezel left edge x 180.5 on the pivot row gives 13.872 px/mm (39 mm anchor, 270.5 px = 19.5 mm) |
| Rings (r px about the dial circle) | black dial and minute track to 191.5, grey rehaut ring 192..213, bezel_in 214, black insert 214..261 (numerals 10..50, bar markers, red triangle with a pearl at 12: all in the photo), steel coin-edge ring 261..270.5 = bezel_out |
| Bezel | rotating, black insert inside a steel coin-edge ring |
| Hands (about 10:10:38) | hour 8.76 mm at 304.9 deg (stem half width 0.78 mm, snowflake diamond widest 2.3 mm half width at 6.0 mm, square nub to the tip, lume strip plus diamond); minute 13.01 mm at 64.1 deg (blade half width 0.62 mm, pointed tip, lume strip); seconds 12.90 mm at 227.8 deg (needle 0.11 mm, counterweight disc 0.51 mm radius at 4.85 mm behind the hub, lume disc 0.7 mm inside a 0.87 mm gold disc at 7.45 mm); gold with cream lume, hub radius 18 px (1.30 mm) |
| Crown | x 718..755, y 572..662 (radius 3.24 mm, centre 0.29 mm below the pivot row), fluted to x 747 then a rounded cap; no crown guards |
| Case | lugs rise slightly above the round bezel: lug tops y 303 (22.35 mm), lug bottoms y 944 (23.86 mm) |
| Bracelet | five columns: outer (brushed, wide), inner (polished), centre, inner, outer. Vertical joint lines x 388.2 / 429.5 / 470.0 / 512.3 (top), 388.8 / 430.5 / 469.6 / 510.6 (bottom). Outer joints top y 238 / 177 (end 142), bottom 1025 / 1084 (end 1123.5); inner top 330 / 266.5 / 202 / 156.5, bottom 923.5 / 988.5 / 1051.5 / 1091; centre top 306.5 / 238 / 176, bottom 938 / 1027 / 1085.5 |
| Dial | black glossy, gold minute track, round lume dots 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11, bar indices 3 / 9 / 6, triangle 12, TUDOR shield, GENEVE, 200m=660ft, MASTER CHRONOMETER, SWISS MADE; no date window; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines and lume polygons measured from the photo (profile and lume lists in the spec) |
| Bezel numerals, markers, dial print | flat in the photo (projected / dial map), not applied geometry |
| Bracelet | `strap.bracelet.columns` / `bounds_x_mm` / `pieces_mm` in the spec describe any column layout |
| Pose | 10:10:38 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, camera 27.744 px/mm centred on the pivot (2x photo pivot (902, 1226) at (1024, 1024), offset (+122, -202)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bb58_prep m7939a1a0nu-0001   # -> 2x reference, config/watches/tudor-bb58-m7939a1a0nu-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
