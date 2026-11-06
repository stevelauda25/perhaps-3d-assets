# Reference plan: TUDOR Royal 40 M2840D1A0-0001 (steel, black sunburst dial, applied baton indices, day-date, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal 36 builds ([-0101](../tudor-royal-36-m2836c1a0-0101/REFERENCE_PLAN.md) black/Roman, [-0103](../tudor-royal-36-m2836c1a0-0103/REFERENCE_PLAN.md) baton dial); this build also sets the **Royal 40 template** for -0002 and -0003.

## Target asset

Front relief GLB `models/watches/tudor-m2840d1a0-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m2840d1a0-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Royal 36 builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Alpha bbox | x 171..762 (762 = crown), y 122..1115 (bracelet runs 487 px above and 506 px below the pivot; the Royal 36 photo has 29.75 / 32.5 mm, here 35.0 / 36.3 mm) |
| Pivot, scale | (450, 609); case left edge x 172 on the pivot row gives 13.9 px/mm (40 mm anchor); same photo scale as the Royal 36 (14.06) |
| Rings (r from pivot) | bezel_out 275, bezel_in 232 (facet inner end), crystal_edge 228, dial_flat 205 (black rehaut band to 215 and a polished inner ring 215..232 are in the dial map) |
| Bezel | 48 segments (FFT of the bezel brightness: 24 cycles per turn); plain facets centred at 0, 15, 30 ... deg (same phase as the Royal 36), ribbed facets with 5 ribs between |
| Hands (10:09:xx) | hour 8.28 mm at 304.4 deg, minute 14.03 mm at 63.2 deg, seconds 14.82 mm at 227.95 deg (line fit through the thin hand, passes the pivot within 1 px) |
| Crown | x 726..762, y 562..656 (radius 3.38 mm, centred on the pivot row) |
| Bracelet | brushed row joints (dark joint lines) top y 287, 237, 193.5, 150, end 122; bottom 927, 982.5, 1029.5, 1077, end 1115; polished channel columns x 387.5..417.5 and 480..510 (2.34..4.5 mm), pieces separated by 1..4 px joint lines (lists in the spec) |
| Dial | black sunburst, applied gold baton indices (none at 3: date window; none at 12: MONDAY window), TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, gold minute track; no Roman numerals (confirmed on the photo); all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`steel_photo`) as in -0103 |
| Indices, windows | flat in the map, not applied geometry |
| Bracelet | flat, row joints and polished pieces at the measured positions |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 2048 px square (not 1800) because the bracelet extends 506 px below the pivot; camera 27.8 px/mm centred on the pivot |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0001   # -> 2x reference, config/watches/tudor-royal40-m2840d1a0-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
