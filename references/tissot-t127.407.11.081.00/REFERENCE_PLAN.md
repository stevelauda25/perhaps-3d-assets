# Reference plan: Tissot T127.407.11.081.00 (Gentleman Powermatic 80 Open Heart, 40 mm, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Tissot's official render.

## Target asset

A front-facing GLB in `models/watches/tissot-t127.407.11.081.00.glb`: front relief, flat back, 2.5D depth, modelled case, applied indices, hands, crown, lugs and bracelet in house steel and glass; the dial and the open-heart movement from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1680 × 1680 | `front_official_1680x1680.png` | HAVE (Tissot official), primary for everything |
| 2 | Front of the head | `head_official_1680x1680.png` | HAVE (Tissot official) |
| 3 | Side from 3 o'clock | `side_official_1680x1680.png` | HAVE (Tissot official): heights |
| 4 | Back | `back_official_1680x1680.png` | HAVE, not needed for the flat-backed asset |
| 5 | 3/4 from the left | `angled_2172x3824.jpg` | HAVE (Irsyad): bezel curve, bracelet |

## Scale anchors

| Dimension | Official | Measured at 40 mm (19.67 px/mm) |
| --- | --- | --- |
| Case width | **40 mm** (anchor) | circle on both case flanks, centred 0.03 mm from the hand pivot (842, 844) |
| Lug width | 21 mm | lug gap 20.6 mm |
| Lug to lug | not listed | 47.5 mm in the render, symmetric |
| Thickness | 11.5 mm | front-relief reading |

The render is 19.67 px/mm, below the 2000 px guideline; it is the largest straight-on image Tissot publishes.

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, bezel | Polished round case, wide curved polished bezel | #1, #3 |
| Dial | Grey-taupe sunray, minute track, lume dots, TISSOT 1853, Powermatic 80, Swiss Made, open-heart aperture at 11 | dial map |
| Indices | 12 applied tapered batons: polished frame, brushed centre | #1, hand-aligned crops |
| Hands | Faceted baton hour and minute with a lume strip and a kite tail; thin polished seconds hand with a tail | #1, hand-aligned crops |
| Crown | Fluted crown at 3 | #1 |
| Bracelet | Three columns: brushed outer links (4.0 mm in the render), polished centre pieces (2.1 mm) | #1, joints at 6 o'clock |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Tissot's official render (the supplied photo is angled) |
| Dial colour | Official render (grey-taupe); the supplied photo is warmer |
| Scale | 40 mm case (official) |
| Open-heart aperture | Photo map kept as is under the hands (the modelled hands cover the same pixels); the dial around it cleaned by rotation |
| Covered prints | The first T of TISSOT (seconds hand) is drawn again from the last T |
| Heights | Front-relief reading of the official 11.5 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tissot_t127407_trace   # -> config/watches/tissot-t127.407.11.081.00-trace.json
python3 -B -m pipeline.tissot_t127407_dial    # -> outputs/watches/tissot-t127.407.11.081.00/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-11 | 2 | Black print redrawn sharp at 4x (2720 px dial map), darker ink; batons with a polished frame sloping into a darker brushed channel; photo batons removed from the map. Approved |
