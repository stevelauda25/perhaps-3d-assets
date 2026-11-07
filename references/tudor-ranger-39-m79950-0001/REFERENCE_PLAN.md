# Reference plan: TUDOR Ranger M79950-0001 (39 mm steel, black dial with Arabic numerals, steel three-column bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal builds ([Royal 40 -0001](../tudor-royal-40-m2840d1a0-0001/REFERENCE_PLAN.md)); the Ranger is a different model (case, bezel, crown, hands, bracelet), so this build also sets the **Ranger 39 template** for the beige M79950-0008.

## Target asset

Front relief GLB `models/watches/tudor-m79950-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79950-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Royal builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Alpha bbox | x 182..764 (764 = crown), y 154..1119; the bracelet runs 461 px (33.4 mm) above and 505 px (36.6 mm) below the pivot |
| Pivot, scale | (451, 615); case left edge x 182 on the pivot row gives 13.795 px/mm (39 mm anchor) |
| Rings (r from pivot, diagonals) | dial_flat 213 (end of the black dial), chamfer / rehaut ring 216..235 (grey gradient, in the dial map), bezel_in 235, flat brushed bezel top 237..266, bezel_out 267 |
| Bezel | smooth fixed bezel: flat brushed top, polished chamfer toward the dial, rounded outer edge; no facets or ribs |
| Hands (10:09:xx) | hour 9.39 mm at 302.7 deg (stem, spear head with cream lume, widest 3.5 mm at 5.3 mm); minute 14.07 mm at 63.7 deg (sword, 1.3 mm wide, lume strip, pointed tip); seconds 15.2 mm at 228.1 deg (needle 0.3 mm, lume block 7.8..10.5 mm along, red tip end; tail 4.6 mm); hub radius 20 px (1.45 mm) |
| Crown | x 722..764, y 578..669 (radius 3.34 mm, centre 0.65 mm below the pivot row), fluted |
| Case | lug tops y 311 (22.05 mm) and lug bottoms y 948 (24.1 mm); case 39 mm wide at the pivot row |
| Bracelet | three brushed columns, no polished pieces: outer columns joints y 313, 212.5 (top) and 944.5, 1047, 1109 (bottom); centre column joints 329.5, 284.5, 186 (top) and 919, 983, 1072.5 (bottom); vertical joint lines x 381.5 / 518.5 (top), converging to 384.5 / 514 at the bottom end |
| Dial | black matte, large Arabic numerals 12 / 3 / 6 / 9 (cream lume), cream baton indices, minute track, TUDOR shield, GENEVE, RANGER, SWISS MADE; no date window; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines measured from the photo (profile lists in the spec) |
| Numerals, indices | flat in the map, not applied geometry |
| Bracelet | flat, three columns with the measured joints and converging vertical joint lines |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, camera 27.59 px/mm centred on the pivot (2x photo pivot (902, 1230) at (1024, 1024)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_ranger39_prep m79950-0001   # -> 2x reference, config/watches/tudor-ranger39-m79950-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
