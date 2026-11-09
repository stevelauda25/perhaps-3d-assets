# Reference plan: Seiko 5 Automatic SNXG47K1 (white woven dial, gold batons, steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Build structure follows the [SNKM87K1](../seiko-snkm87k1/REFERENCE_PLAN.md).

## Target asset

A front-facing GLB in `models/watches/seiko-snxg47k1.glb`: front relief, flat back, 2.5D depth, case/indices/hands/day-date frame/crown/bracelet as geometry, dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned about 15° toward the crown, 3000 × 4851 | `front_3000x4851.png` | HAVE, sharp; straightened on the dial plane for the dial map, hands and indices |
| 2 | Front, straight-on, 2000 × 2000 (watch about 980 px wide) | `front_straight_2000x2000.jpg` | HAVE: case, lug and bracelet outline, crown position |
| 3 | Back | `back_2000x2000.jpg` | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **38 mm** | Irsyad's listing (other listings: 37 mm) |
| Lug width | 16 mm listed | measured 18.2 mm bracelet next to the case, 20.3 mm between the hood corners; not matched |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, wide polished bezel; polished hooded case: lug tips at 22.9 mm, the hood fills the space between them | #2 |
| Crown | Small knurled crown at about 4 o'clock (114°) | #2 |
| Crystal | Flat, inside a dark gasket at 16.9 mm | #1 |
| Dial | White, fine woven pattern (period 0.48 mm), black minute ticks; flat to 16.0 mm | #1, map |
| Hour indices | Faceted gold batons 10.1–14.3 mm, 0.54 mm wide; double at 12; none at 3 | #1 |
| Logo, print | Applied gold `SEIKO` and 5 shield, `AUTOMATIC`, small print at 6: in the dial map. The seconds hand crosses the `K`, which is redrawn from the same logo on the SNKL50K1 dial | #1 |
| Day-date | `WED 16`, wide gold frame 8.7 × 3.6 mm | #1 |
| Hands | Gold baton hour (7.71 mm) and minute (13.05 mm) with pointed tips and a cream lume window; gold needle seconds hand (13.3 mm) with a paddle tail; gold hub | #1 |
| Bracelet | Three columns, centre half the width, centre links half a row off the outer links; rows 4.07 mm | #2 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snxg47_rectify   # -> outputs/watches/seiko-snxg47k1/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snxg47_trace     # -> config/watches/seiko-snxg47k1-trace.json
python3 -B -m pipeline.seiko_snxg47_dial      # -> outputs/watches/seiko-snxg47k1/dial_photo.jpg (regenerated, not committed)
```

The straightening maps the eleven baton tips to one circle (residuals 1–8 px). Scale 62.5 px/mm on the straightened photo, tied to the 38 mm case through the straight photo (case flank / baton tip = 1.319). Hands read 10:09:01.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snxg47k1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-snxg47k1/)
```

| Date | Change |
| --- | --- |
| 2026-11-09 | First front relief with the house values (2.5D depth 0.35, 7 mm curl from the lug tips, glass, steel textures); hub 0.96 mm to cover the gold collar; 1.6 MB GLB, committed to `models/watches/seiko-snxg47k1.glb` |

## Known gaps

- No sharp straight-on photo: the dial is straightened from a turned photo; raised parts keep about 0.4 mm of parallax.
- Lug width: listing says 16 mm, the photo shows about 18 mm.
- Heights are the SNKM87K1 values (listed 12 mm thick), not measured.
