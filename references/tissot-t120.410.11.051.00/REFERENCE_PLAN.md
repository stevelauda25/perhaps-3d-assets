# Reference plan: Tissot T120.410.11.051.00 (Seastar 1000 Quartz, 40 mm, black dial, black insert, steel bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Tissot's official render.

## Target asset

A front-facing GLB in `models/watches/tissot-t120.410.11.051.00.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, indices, date frame, hands, crown, lugs and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1680 × 1680 | `front_official_1680x1680.png` | HAVE (Tissot official), primary for everything |
| 2 | Front of the head | `head_official_1680x1680.png` | HAVE (Tissot official) |
| 3 | Side from 3 o'clock | `side_official_1680x1680.png` | HAVE (Tissot official): heights |
| 4 | Back | `back_official_1680x1680.png` | HAVE, not needed for the flat-backed asset |
| 5 | 3/4 from the left | `angled_supplied_933x1200.jpg` | HAVE (Irsyad): bezel, bracelet |

## Scale anchors

| Dimension | Official | Measured at 40 mm (19.64 px/mm) |
| --- | --- | --- |
| Case width | **40 mm** (anchor) | coin-edge circle on both flanks, centred 0.3 mm below the hand pivot |
| Lug width | 20 mm | end link 20.4 mm |
| Lug to lug | not listed | 45.3 mm in the render (tips 22.3 mm top, 23.0 mm bottom) |
| Thickness | 9.97 mm | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel ring with a coin edge (90 teeth); black insert with a white triangle at 12, 10 20 30 40 50, bars and minute marks 1-14; polished inner lip | #1; prints traced by threshold |
| Case, lugs | Round case under the bezel; broad lugs with a chamfered tip; one crown guard round the crown at 3 | #1 silhouette and crops |
| Dial | Black, minute track at the edge, grey sloped flange; TISSOT 1853, SEASTAR, 30 bar (300m / 1000 ft), SWISS MADE | dial map |
| Indices | Applied: polished frame round lume; round dots, triangle at 12, bars at 3 and 9; polished date frame at 6. Centred 0.34 mm below the hand pivot | #1, threshold and crops |
| Hands | Baton hour and minute hands with a pointed tip and a lume panel in a polished frame; tails below the hub; polished seconds needle, lume dot in a ring, T-shaped counterweight | #1, axis profiles and gridded crops |
| Crown | Fluted crown at 3 | #1 |
| Bracelet | Three columns: brushed outer links (5.8 mm pitch), polished centre links (4.9 mm pitch), centre joints 2.0 mm nearer the case | #1 joints at 6 and 12 |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Tissot's official render (the supplied photo is angled) |
| Scale | 40 mm case width (official) |
| Insert | One flat black colour; prints as white inlays |
| Heights | Front-relief reading of the official 9.97 mm |
| Hand pose | The render's pose (about 10:08:37) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Dial under the hands | Smooth inpaint of the black dial (every filled pixel lies under a 3D hand or index); the flange and minute track are filled by 6 deg rotations |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tissot_t120410_trace   # -> config/watches/tissot-t120.410.11.051.00-trace.json
python3 -B -m pipeline.tissot_t120410_dial    # -> outputs/watches/tissot-t120.410.11.051.00/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
