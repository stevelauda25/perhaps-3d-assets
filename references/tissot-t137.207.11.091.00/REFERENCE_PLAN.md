# Reference plan: Tissot T137.207.11.091.00 (PRX Powermatic 80, 35 mm, green waffle dial, integrated bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Tissot's official render.

## Target asset

A front-facing GLB in `models/watches/tissot-t137.207.11.091.00.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, batons, date frame, hands, crown and integrated bracelet; the waffle dial from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1680 × 1680 | `front_official_1680x1680.png` | HAVE (Tissot official), primary for everything |
| 2 | Head only, straight-on | `head_official_1680x1680.png` | HAVE (Tissot official) |
| 3 | Side from 3 o'clock | `side_official_1680x1680.png` | HAVE (Tissot official): heights |
| 4 | Back | `back_official_1680x1680.png` | HAVE, not needed for the flat-backed asset |
| 5 | 3/4 close-up | `detail_angled_1500x1500.png` | HAVE (Tissot official): flank, bezel, links |
| 6 | 3/4 from the left | `angled_650x800.jpg` | HAVE (Irsyad) |

## Scale anchors

| Dimension | Official | Measured at 35 mm (19.6 px/mm) |
| --- | --- | --- |
| Case width | **35 mm** (anchor) | twice the widest left half width, hand pivot (840, 838) |
| Case length | 35 mm | 34.0 mm between the case edges where the first links start |
| Thickness | 10.93 mm | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Brushed top, flanks running straight into the bracelet, polished edges | #1, left half of the alpha mirrored (the right half has the crown and the drop shadow) |
| Bezel | Wide, polished, 14.9 to 16.6 mm radius | #1, radial profiles |
| Dial | Green waffle (square grid), white minute track and prints, date at 3 | dial map |
| Indices | Applied polished batons, double at 12, none at 3, a lume inset at the inner end | #1 |
| Date | Polished applied frame | #1 |
| Hands | Faceted batons with a lume strip and a short tail; thin seconds hand with counterweight | #1, straightened strips |
| Crown | Fluted, at 3 | #1 |
| Bracelet | Integrated H-link, tapering; outer pieces start with a short link, centre pieces offset by half a link | #1, joints on both ends |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Tissot's official render (the supplied photo is angled) |
| Scale | 35 mm case width (official) |
| Hand removal | Quarter turns only (the grid is square and centred on the pivot); next to the hub a waffle patch from the best-matching spot |
| Dial print | White print redrawn at 4x the render's resolution |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tissot_t137207_trace   # -> config/watches/tissot-t137.207.11.091.00-trace.json
python3 -B -m pipeline.tissot_t137207_dial    # -> outputs/watches/tissot-t137.207.11.091.00/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build. Approved |
