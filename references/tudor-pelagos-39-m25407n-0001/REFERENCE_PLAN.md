# Reference plan: TUDOR Pelagos 39 M25407N-0001 (39 mm titanium, black dial, three-column titanium bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal, Ranger, Black Bay 54 and Black Bay 58 builds ([Black Bay 58 -0001](../tudor-black-bay-58-m7939a1a0nu-0001/REFERENCE_PLAN.md)); the Pelagos 39 is a new model (titanium, black insert dive bezel with a titanium coin edge, square-shouldered snowflake hands, crown-guard shoulder, three-column bracelet), so this build sets the **Pelagos 39 template**.

## Target asset

Front relief GLB `models/watches/tudor-m25407n-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet. Only what the photo shows is built: the folding clasp extension of the real bracelet is not in the photo and is not modelled.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow and a corner logo, 900 x 1200 | `tudor-m25407n-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay 58 build, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub pin hole)

| Item | Result |
| --- | --- |
| Alpha | watch = largest component, bbox x 179..763 (763 = crown), y 128..1121; the GPHG logo (x 627..856, y 898..1115) is a set of separate components |
| Pivot, scale | hub pin hole (449, 594) (read at 12x); circle fits on the insert's outer edge (r 256.5) and the crystal rim (r 199.6) are centred at (449.1, 594.0), so no ring shift. Coin-edge teeth tips radius 270.8 gives 13.887 px/mm (39 mm anchor, 19.5 mm radius) |
| Rings (r px about the pivot) | black dial and minute track to 191.5, grey rehaut ring 192..194, bright crystal rim 199..205 (crystal_edge 205), bezel_in 205.5, black insert 205.5..256.5 (numerals 10..50, bar markers, white triangle with a pearl at 12: all in the photo), titanium coin-edge ring 257..270.8 = bezel_out |
| Bezel | rotating, black insert inside a titanium coin-edge ring |
| Hands (about 10:08:30) | hour 8.16 mm at 303.7 deg (stem half width 0.64 mm, square-shouldered diamond widest 2.1 mm half width at 5.8 mm, square nub to 8.16 mm, symmetric); minute 12.56 mm at 62.9 deg (blade half width 0.53..0.57 mm, square-cut tip, tip against the 2 o'clock index); seconds 12.7 mm at 186.0 deg (needle half width 0.15 mm, lume diamond half diagonal 1.1 mm at 7.6 mm, counterweight bar 4.0 mm behind the hub, half width 0.42 mm); hub radius 16 px (1.15 mm) |
| Crown | x 713..763, y 551..643 (radius 3.31 mm, centre 0.22 mm below the pivot row), fluted to x 751 then a rounded cap; a crown-guard shoulder of the case reaches x 735 above it (y 516..548) |
| Case | lugs flare out of the bracelet width at y 291 (top, 21.82 mm) and y 908 (bottom, 22.61 mm) |
| Bracelet | three columns: outer, centre (wide), outer; vertical joint lines x 381.7 / 516.6 (top), 382.5 / 517.4 (bottom). Outer joints top 202 / 140 (end 129), bottom 1013 / 1091.5 (end 1121.5); centre top 246.5 / 166, bottom 875 / 961 / 1056.5 / 1112.5 (end 1122) |
| Dial | black matte sunburst, rectangular and square lume indices (bars 3 / 9 / 6, triangle 12, squares elsewhere), minute track dots, TUDOR shield, GENEVE, red PELAGOS, 200m = 660ft, CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE; no date window; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines and lume polygons measured from the photo (profile and lume lists in the spec) |
| Bezel numerals, markers, dial print | flat in the photo (projected / dial map), not applied geometry |
| Bracelet | `strap.bracelet.columns` / `bounds_x_mm` / `pieces_mm` in the spec describe the three columns |
| Pose | 10:08:30 as photographed; front-locked presentation |
| Comparison frame | 2176 px square, camera 27.7744 px/mm centred on the pivot (2x photo pivot (898, 1188) at (1088, 1088), offset (+190, -100)); 2176 because the bracelet end is 527 px (1x) below the pivot |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_pelagos39_prep m25407n-0001   # -> 2x reference, config/watches/tudor-pelagos39-m25407n-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
