# Reference plan: Tissot T120.407.17.041.00 (Seastar 1000 Powermatic 80, 43 mm, blue gradient dial, black ceramic insert, rubber strap)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is 1024 px; the straight front is Tissot's official render.

## Target asset

A front-facing GLB in `models/watches/tissot-t120.407.17.041.00.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, indices, hands, crown, lugs and rubber strap in house steel and glass; the dial print and the strap from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1680 × 1680 | `front_official_1680x1680.png` | HAVE (Tissot official), primary for everything |
| 2 | Side from 3 o'clock | `side_official_1680x1680.png` | HAVE (Tissot official): heights |
| 3 | Back | `back_official_1680x1680.png` | HAVE, not needed for the flat-backed asset |
| 4 | Front, retailer photo, 1024 × 1024 | `front_supplied_1024x1024.jpg` | HAVE (Irsyad): colour check only |

## Scale anchors

| Dimension | Official | Measured at 43 mm (19.43 px/mm) |
| --- | --- | --- |
| Case width | **43 mm** (anchor) | coin-edge circle on both flanks, centred 0.2 mm from the hand pivot |
| Lug width | 21 mm | lug gap 20.6 mm; strap 21.3 mm at the lug tips, tapering to 18.4 mm |
| Lug to lug | not listed | 49.6 mm in the render (tips 24.6 mm top, 25.0 mm bottom) |
| Thickness | 12.7 mm | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel ring with a coin edge (90 square teeth); black ceramic insert with a silver triangle and lume pip at 12, 10 20 30 40 50, bars and minute marks 1-14; polished inner lip | #1; prints traced by threshold |
| Case, lugs | Round case under the bezel; broad lugs with a chamfered tip; one crown guard round the crown at 3 | #1 silhouette and crops |
| Dial | Blue gradient (dark rim), black flange with minute track; TISSOT 1853, SEASTAR, POWERMATIC 80, 30 bar (300m / 1000 ft), SWISS MADE; round date window at 6 | dial map |
| Indices | Applied: polished frame round lume; round dots, triangle at 12, bars at 3 and 9, short bar at 6. Centred 0.14 mm right of and 0.1 mm below the hand pivot | #1, threshold and crops |
| Hands | Broad baton hour and minute hands with a pointed tip and a lume panel in a polished frame; tails below the hub; polished seconds needle, lume dot in a ring, T-shaped counterweight | #1, axis profiles and gridded crops |
| Crown | Fluted crown at 3 | #1 |
| Strap | Black rubber with a recessed panel, tapering | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Tissot's official render (the supplied photo is 1024 px) |
| Scale | 43 mm case width (official) |
| Insert | One flat black ceramic colour; prints as silver inlays |
| Heights | Front-relief reading of the official 12.7 mm |
| Hand pose | The render's pose (about 10:09:35) |
| Strap curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Dial under the hands | Smooth inpaint of the gradient (every filled pixel lies under a 3D hand or index); the flange is filled by 6 deg rotations |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tissot_t120407_trace   # -> config/watches/tissot-t120.407.17.041.00-trace.json
python3 -B -m pipeline.tissot_t120407_dial    # -> outputs/watches/tissot-t120.407.17.041.00/dial_photo.jpg, strap.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
