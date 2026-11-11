# Reference plan: Bulova 98A273 (Marine Star Automatic 44 mm, gold tone, black dial, open heart)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Bulova's official render.

## Target asset

A front-facing GLB in `models/watches/bulova-98a273.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, screws, hands, crown, lugs and bracelet in house glass and a gold-tone metal; the dial from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1347 × 2048 | `front_official_1347x2048.png` | HAVE (Bulova official), primary for everything |
| 2 | Side, crown side | `side_official_1707x2048.png` | HAVE (Bulova official): heights |
| 3 | Back | `back_official_1848x2048.png` | HAVE (Bulova official), not needed for the flat-backed asset |
| 4 | 3/4 from the left | `angled_1200x1200.jpg` | HAVE (Irsyad): ring and bezel slope |

## Scale anchors

| Dimension | Official | Measured at 44 mm (27.17 px/mm) |
| --- | --- | --- |
| Case width | **44 mm** (anchor) | black ring silhouette at 9 and 3 o'clock |
| Lug width | 24 mm | bracelet 23.5 mm |
| Case length | 51 mm | 50.9 mm (lug tip to lug tip) |
| Thickness | 13.45 mm | side view: gold bezel about 2.0 mm, black ring 1.6 mm, case, case back |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, lugs | Gold, brushed, angular lugs, crown guards at 3 | #1 silhouette, #2 |
| Black ring | Black PVD polygon ring under the bezel, gold case showing in its corner notches | #1 traced per degree |
| Bezel | Round gold bezel: polished inner slope, brushed flat top, six black hex screws | #1, #2 |
| Dial | Black sunray dial, flat octagon centre, chapter ring with minute numerals, prints, subdial at 4, open heart at 7-8 | dial map |
| Applied | Gold Roman numerals and Bulova logo, gold subdial and open-heart rings | #1 gold mask, traced outlines |
| Hands | Gold-framed sword hour and minute hands with lume and an open window; small seconds hand | #1, hand-aligned strips |
| Crown | Fluted gold crown at 3 between guards | #1 |
| Bracelet | Five columns: outer and centre links in step, middle links half a row nearer the case | #1, dark joint rows per column |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Bulova's official render (the supplied photo is angled) |
| Scale | 44 mm case width (official) |
| Link pitch | 5.2 mm from the 6 o'clock side (the 12 o'clock side is more foreshortened) |
| Covered parts | II under the minute hand: completed from its mirror image |
| Heights | Front-relief reading of the official 13.45 mm and side view |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_98a273_trace   # -> config/watches/bulova-98a273-trace.json
python3 -B -m pipeline.bulova_98a273_dial    # -> outputs/watches/bulova-98a273/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
