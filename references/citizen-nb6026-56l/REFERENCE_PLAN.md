# Reference plan: Citizen NB6026-56L (Promaster Fujitsubo, 41 mm titanium, blue dial, black insert, blue bezel ring, titanium bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)).

## Target asset

A front-facing GLB in `models/watches/citizen-nb6026-56l.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, applied indices, hands, crown, lugs and bracelet in house steel and glass; the dial from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1324 × 2048 | `front_official_1324x2048.png` | HAVE (Citizen official), primary for everything |
| 2 | Side from 9 o'clock | `side_official_1524x2048.png` | HAVE (Citizen official): heights |
| 3 | Back | `back_official_1465x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | Line drawing of the front | `diagram_official_1365x2048.png` | HAVE (Citizen official) |
| 5 | Front, retailer photo | `front_supplied_1853x3107.jpg` | HAVE (Irsyad): colour check |

## Scale anchors

| Dimension | Listed | Measured at 41 mm (28.55 px/mm) |
| --- | --- | --- |
| Case width | **41 mm** (anchor) | the blue coin-edge bezel, centred 0.12 mm below the hand pivot |
| Lug width | 20 mm | bracelet 19.4 mm at the lug tips (listings measure between the lugs) |
| Lug to lug | not listed | 47.7 mm in the render (tips 23.0 mm top, 24.7 mm bottom: the render is slightly perspective) |
| Thickness | 12.2 mm | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Blue anodised ring with a wavy coin edge; black insert with grained silver 10-50 numerals, bars, 1-14 minute dots and a triangle with a lume pip | #1; prints traced by threshold |
| Case, lugs | Round case under the overhanging bezel, broad lugs | #1 silhouette |
| Dial | Blue gradient; CITIZEN AUTOMATIC, DIVER'S 200m TITANIUM; date at 3; minute track; crystal chamfer reflections at the rim | dial map |
| Indices | Applied rectangles: polished frame round lume; wider at 12, 6 and 9; a short one beside the date at 3 | #1, threshold |
| Hands | Hour: slotted shaft, ring with a three-spoke lume disc, pointed lume tip. Minute: baton with a lume panel, pointed. Seconds: needle with a short tail and a lume dot in a ring | #1, axis profiles and gridded crops |
| Crown | Fluted crown at 3 | #1 |
| Bracelet | Three columns: brushed outer links (5.2 mm pitch), wide polished centre links (5.0 mm pitch) | #1 joints at 6 (the 12 end is foreshortened) |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Citizen's official render (cleaner than the supplied photo, same view) |
| Scale | 41 mm = the coin-edge bezel (case width as listed) |
| Materials | Titanium shown with the house steel materials; blue ring anodised blue |
| Heights | Front-relief reading of the listed 12.2 mm |
| Hand pose | The render's pose |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Dial under the hands and indices | Smooth fill of the gradient inside the minute track; the track and rim copied by 6 deg rotations |

## Phase 1 outputs

```sh
python3 -B -m pipeline.citizen_nb6026_trace   # -> config/watches/citizen-nb6026-56l-trace.json
python3 -B -m pipeline.citizen_nb6026_dial    # -> outputs/watches/citizen-nb6026-56l/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
