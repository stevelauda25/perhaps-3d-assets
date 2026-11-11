# Reference plan: Bulova 98A227 (Marine Star automatic, 44 mm, rose-gold tone, blue silicone strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Bulova's official render.

## Target asset

A front-facing GLB in `models/watches/bulova-98a227.glb`: front relief, flat back, 2.5D depth, modelled case, ring, bezel, screws, applied numerals, hands and crown; the dial, the open-heart movement and the strap from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1390 × 2048 | `front_official_1390x2048.png` | HAVE (Bulova official), primary for everything |
| 2 | Side from 9 o'clock | `side_official_1653x2048.png` | HAVE (Bulova official): heights |
| 3 | Back | `back_official_1164x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | 3/4 from the left | `angled_1000x1433.jpg` | HAVE (Irsyad): ring, bezel, lugs |

## Scale anchors

| Dimension | Official | Measured at 44 mm (27.18 px/mm) |
| --- | --- | --- |
| Case width | **44 mm** (anchor) | across the blue ring at 9 o'clock and its mirror, hand pivot (633, 1021) |
| Lug width | 24 mm | strap 23.8 mm |
| Lug to lug | not listed | 50.1 mm in the render |
| Thickness | 12 mm | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Rose-gold tone, faceted lugs, crown guards | #1, alpha outline |
| Outer ring | Blue, 24 sides | #1, colour mask per angle |
| Bezel | Brushed rose gold, 16.4 to 21.1 mm radius, a V notch in its outer edge at every ring vertex, six blue screws | #1 |
| Dial | Blue with radial ridges, chapter ring with minutes, prints, sub-seconds at 4, open heart at 7 | dial map |
| Applied | Rose-gold Roman numerals and the Bulova logo; rings round the sub-seconds and the open heart | #1, colour mask outlines |
| Hands | Rose-gold sword hands with lume and an open slot; red sub-seconds hand with a wide tail | #1, gridded crops |
| Crown | Fluted rose-gold crown at 3 | #1 |
| Strap | Blue textured silicone, red underside | strap map, house curl |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Bulova's official render (the supplied photo is angled) |
| Scale | 44 mm case width (official) |
| Applied numerals | Outlines traced from the render's rose-gold colour; where a hand covers a numeral the outline follows the hand edge (hidden under the hand) |
| Open heart | Movement from the dial map; the hands do not cross it |
| Heights | Front-relief reading of the official 12 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_98a227_trace   # -> config/watches/bulova-98a227-trace.json
python3 -B -m pipeline.bulova_98a227_dial    # -> outputs/watches/bulova-98a227/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
