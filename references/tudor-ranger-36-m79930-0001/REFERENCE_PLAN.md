# Reference plan: TUDOR Ranger 36 M79930-0001 (36 mm steel, black dial with Arabic numerals, steel three-column bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe and design as the [Ranger 39 M79950-0001](../tudor-ranger-39-m79950-0001/REFERENCE_PLAN.md) (smaller size), re-measured on this photo: none of the 39's numbers were reused.

## Target asset

Front relief GLB `models/watches/tudor-m79930-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79930-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Ranger 39 / Royal builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 199..745 (745 = crown), y 240..1120; the bracelet runs 427 px (30.5 mm) above and 453 px (32.4 mm) below the pivot |
| Pivot, scale | hub hole (451.5, 667) taken as (451, 667); case left edge x 199 on the pivot row gives 14.0 px/mm (36 mm anchor). The dial/bezel circle is centred at (449.8, 666.6), 1.2 px left of the pivot |
| Rings (r from the ring centre) | dial_flat 200 (end of the black dial print), grey rehaut 201..212 (crystal_edge 213), dark gap 213..215, polished chamfer 216..219 (bezel_in 215), flat brushed top 220..248 (bezel_out 249); silhouette at 250.8 |
| Bezel | smooth fixed bezel, flat brushed top, polished chamfer toward the dial, rounded outer edge (narrower than the 39: 34 px against 32 px at 13.8 px/mm scale, same design) |
| Hands (10:09:xx) | hour 8.78 mm at 304.7 deg (stem half width 0.64 mm, spear head widest 3.1 mm at 5.2 mm, cream lume); minute 13.1 mm at 62.0 deg (sword, 1.18 mm wide, cream lume strip 1.7..9.3 mm, pointed tip); seconds 13.06 mm at 228.5 deg (needle 0.25 mm, lume block 7.5..9.5 mm, red end; stub tail 4.24 mm); hub radius 19 px (1.36 mm) |
| Crown | x 703..746, y 624..711 (radius 3.1 mm, centred on the pivot row), fluted (about 36 flutes, pitch 0.5 mm), narrow neck, rounded end cap from x 740 |
| Case | lug tops y 369 (21.3 mm) and lug bottoms y 970 (21.6 mm); 36 mm wide at the pivot row |
| Bracelet | three brushed columns, no polished pieces: outer columns joints y 369, 285 (top) and 967, 1043, 1097.5 (bottom); centre column joints 388, 345, 263 (top) and 946.5, 993, 1059, 1111 (bottom, thin end piece 1111..1120); vertical joint lines x 381.3 / 516.0 (top), 380 / 516 (bottom), converging slightly at the bottom end |
| Dial | black matte, large Arabic numerals 12 / 3 / 6 / 9 (cream lume), cream baton indices, minute track, TUDOR shield, GENEVE, RANGER, SWISS MADE; no date window; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines measured from this photo |
| Numerals, indices | flat in the map, not applied geometry |
| Bracelet | flat, three columns with the measured joints and vertical joint lines |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, camera 28.0 px/mm centred on the pivot (2x photo pivot (902, 1334) at (1024, 1024), offset (+122, -310)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_ranger39_prep m79930-0001   # registry m79930 -> tudor-ranger-36 / tudor-ranger36; writes the 2x reference, config/watches/tudor-ranger36-m79930-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
