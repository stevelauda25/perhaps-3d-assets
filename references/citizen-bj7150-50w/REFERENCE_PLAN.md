# Reference plan: Citizen BJ7150-50W (Promaster Land GMT, 39.5 mm, red textured dial, steel 24-hour bezel, steel bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)).

## Target asset

A front-facing GLB in `models/watches/citizen-bj7150-50w.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, hands, crown, lugs and bracelet in house steel and glass; the dial from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1295 × 2048 | `front_official_1295x2048.png` | HAVE (Citizen official), primary for everything |
| 2 | Side from 9 o'clock | `side_official_1556x2048.png` | HAVE (Citizen official): heights |
| 3 | Back | `back_official_1447x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | Line drawing of the front | `diagram_official_1365x2048.png` | HAVE (Citizen official) |
| 5 | Front, retailer photo | `front_supplied_1249x2048.jpg` | HAVE (Irsyad): colour check |

## Scale anchors

| Dimension | Listed | Measured at 39.5 mm (27.14 px/mm) |
| --- | --- | --- |
| Case width | **39.5 mm** (anchor) | the steel bezel's outer edge; the case flanks measure 41.6 mm |
| Lug width | 20 mm | bracelet 20.1 mm at the lug tips |
| Lug to lug | not listed | 45.8 mm in the render |
| Thickness | 13.5 mm | front-relief reading |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Fixed satin steel ring, chamfered edges, black 24-hour numerals and marks | #1; prints traced by threshold |
| Case, lugs | Round case wider than the bezel, broad lugs, bulge round the crown at 3 | #1 silhouette and crops |
| Dial | Red textured dial; printed lume Arabic numerals, triangle at 12, bars at 3 6 9; CITIZEN, Eco-Drive GMT; date at 3; red sloped flange with white marks | dial map |
| Hands | Hour: shaft with a lume panel, a barb, pointed blade with lume. Minute: baton with lume, pointed. Seconds: white needle with an oval counterweight. GMT: yellow with an outlined lume triangle. Black hub | #1, axis profiles and gridded crops |
| Crown | Knurled crown at 3 | #1 |
| Bracelet | Three columns: brushed outer links (5.8 mm pitch), wide polished centre links (5.2 mm pitch); the centre end piece reaches 2.8 mm past the lug tips | #1 joints at 12 and 6 |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Citizen's official render (cleaner than the supplied photo, same view) |
| Scale | 39.5 mm = the bezel (case width as listed); cross-checked by the 20 mm bracelet |
| Dial numerals | Printed lume: kept in the dial map |
| Heights | Front-relief reading of the listed 13.5 mm |
| Hand pose | The render's pose |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Dial under the hands | Copied from the same radius a few degrees away (the texture has no direction); the hub zone inpainted under the black hub |

## Phase 1 outputs

```sh
python3 -B -m pipeline.citizen_bj7150_trace   # -> config/watches/citizen-bj7150-50w-trace.json
python3 -B -m pipeline.citizen_bj7150_dial    # -> outputs/watches/citizen-bj7150-50w/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
