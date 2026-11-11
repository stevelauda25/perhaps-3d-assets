# Reference plan: Bulova 96A225 (Lunar Pilot, 45 mm chronograph, black dial, tachymeter, black NATO strap)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)).

## Target asset

A front-facing GLB in `models/watches/bulova-96a225.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, indices, hands, crown and strap shape in house steel and glass; the dial and the NATO strap from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1208 × 2048 | `front_official_1208x2048.png` | HAVE (Bulova official), primary for everything |
| 2 | Side from 3 o'clock | `side_official_1448x2048.png` | HAVE (Bulova official): heights, pushers |
| 3 | Back | `back_official_1127x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | Line drawing of the front | `diagram_official_1365x2048.png` | HAVE (Bulova official) |
| 5 | Front, retailer photo | `front_supplied_2216x3809.jpg` | HAVE (Irsyad): colour check |

## Scale anchors

| Dimension | Listed | Measured at 45 mm (24.02 px/mm) |
| --- | --- | --- |
| Case width | **45 mm** (anchor) | twice the left flank's widest half from the hand pivot |
| Lug width | 20 mm | NATO strap 19.7 mm |
| Case length | 52.8 mm | 52.3 mm in the render |
| Thickness | 10.3 mm (official; reviews say 13.5) | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Polished asymmetric cushion case, pushers at 2 and 4 in the right flank, fixed strap bars under the case ends | #1 silhouette |
| Bezel | Thin polished ring round the black tachymeter ring | #1 |
| Dial | Black; BULOVA; subdials at 9, 3, 6 with concentric grooves; 262 kHz; minute-track flange; black tachymeter ring with white scale | dial map |
| Indices | Applied: polished frame round lume; double bar at 12, wide blocks at 3 6 9, bars elsewhere; centred 0.18 mm below the pivot | #1, threshold and crops |
| Hands | White lume batons in polished frames; white chrono needle with a lozenge and a wide tail; white subdial needles | #1, axis profiles and gridded crops |
| Crown | Large fluted crown at 3 | #1 |
| Strap | Black nylon NATO with steel keepers | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Bulova's official render (transparent, same view as the supplied photo) |
| Scale | 45 mm case width, left flank mirrored (the right flank carries the crown and pushers) |
| Heights | Front-relief reading of the official 10.3 mm |
| Hand pose | The render's pose |
| Strap curve | House curl: 7 mm radius from the case edges, end_y = edge + 2.2 R |
| Dial under the hands | Subdials and rings copied by rotation; the plain black dial filled from the dial around |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_96a225_trace   # -> config/watches/bulova-96a225-trace.json
python3 -B -m pipeline.bulova_96a225_dial    # -> outputs/watches/bulova-96a225/dial_photo.jpg, strap.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
