# Reference plan: Orient RA-AA0818L19B (Mako III, blue sunburst dial, two-tone blue insert, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/orient-ra-aa0818l19b.glb`, built like `orient-ra-ac0q17y.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, indices, numerals, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1700 × 2715 | `front_1700x2715.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 12.8 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 41.8 mm (34.42 px/mm) |
| --- | --- | --- |
| Case width | **41.8 mm** (anchor, listing) | case flanks at 3 and 9, centred 0.3 mm below the hand pivot (787, 1318) |
| Bezel | not listed | scalloped edge 40.4 mm; insert 32.1-37.1 mm; crystal ring 30.8 mm |
| Lug width | 22 mm | end link 21.6 mm; bracelet 21.5 mm just past the lugs, tapering |
| Lug to lug | 46.8 mm | 45.75 mm (tips 22.4 mm top, 23.4 mm bottom) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel ring with about 110 rounded grip scallops; aluminium insert, light blue from the 12 triangle to 15, dark blue elsewhere; white numerals 10-50, bars, dots 1-14, triangle with a lume pip | #1; prints traced by threshold, colours from the photo median |
| Case, lugs | Round case wider than the bezel at 3 and 9; broad brushed lugs | #1 silhouette |
| Dial | Blue sunburst, darker at the edge; minute track | dial map |
| Numerals, indices | Applied white 12, 6, 9; white bars pointed toward the centre with a polished edge at the other hours | #1; numerals traced |
| Day-date | Polished frame with two windows at 3 | #1; SAT 11 redrawn in the dial map (the minute hand hides their tops) |
| Hands | Hour: leaf, polished outline, black border, lume; minute: long sword, same build; seconds: polished needle, yellow lume triangle and tip, black wedge counterweight | #1 |
| Crown | Large fluted crown at 3, no guards | #1 |
| Bracelet | Three columns, brushed, tapering; centre joints 1 mm nearer the case; pitch 5.2 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 41.8 mm case width (listing); the end link then measures 21.6 mm against 22 mm listed |
| Insert | Geometry in two flat blues (no photo map on the bezel); light sector 0-90 deg of the bezel, turned with the pip (-2 deg) |
| Heights | Front-relief reading of the listed 12.8 mm (no side photo) |
| Hand pose | The pose in #1 (about 10:15:47) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_aa0818l19b_trace   # -> config/watches/orient-ra-aa0818l19b-trace.json
python3 -B -m pipeline.orient_ra_aa0818l19b_dial    # -> outputs/watches/orient-ra-aa0818l19b/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
