# Reference plan: Orient RA-AA0C02L19B (Contemporary automatic, blue sunburst day-date dial, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
the 3/4 photo; the straight front photo comes from a retailer listing of the same reference (see `sources.md`).
House method: modelled case, bezel, crown guards, lugs, crown, indices, day-date frame, hands and bracelet in house steel and
glass; one photo map for the dial print.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2000 × 2000 | `front_2000x2000.jpg` | HAVE, primary for everything (soft fine detail) |
| 2 | 3/4 from the crown side, 1000 × 1568 | `three_quarter_1000x1568.jpg` | HAVE: bezel, guards and bracelet profile, read by eye |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Official | Measured at 41.9 mm (30.26 px/mm) |
| --- | --- | --- |
| Case width | **41.9 mm** (anchor) | 9-3 row, case edge to the crown root |
| Lug to lug | 48.0 mm | 47.0 mm (photo taken a little from below: the lugs sit lower; official value used) |
| Bracelet | 22 mm | end link 21.5 mm |
| Crystal ring | not listed | 37.3 mm (inner edge of the brushed bezel) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, flat brushed bezel flush with the case, crown guards above and below the crown | #1, #2 |
| Lugs | Four brushed lugs with polished edges, straight inner edges | #1 silhouette |
| Dial | Blue sunburst, printed minute track with lume squares, crown emblem, ORIENT Automatic, Water Resistant, movement print, day-date | dial map |
| Indices | Applied rounded bars (polished frame, grey lume) at 1-11, 3 shortened by the day-date, a wider solid faceted bar at 12; polished day-date frame | #1 |
| Hands | Hour and minute swords: polished frame, lume inlay; thin polished seconds with a short tail; stepped hub | #1 |
| Crown | Fluted, smooth end cap, at 3 | #1 |
| Bracelet | Three brushed columns; centre joints between the outer ones; pitch 5.6 mm | #1 bottom side |

## Decisions

| Decision | Answer |
| --- | --- |
| Front photo | Retailer's straight front of the same watch; Irsyad's photo is 3/4 only |
| Scale | Official 41.9 mm case; official 48.0 mm lug to lug |
| Centre | The photo is taken a little from below; the model is symmetric about the index ring centre |
| Heights | Front-relief reading of the official 11.7 mm |
| Hand pose | The pose in #1 so the comparison render lines up |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_aa0c02l19b_trace   # -> config/watches/orient-ra-aa0c02l19b-trace.json
python3 -B -m pipeline.orient_ra_aa0c02l19b_dial    # -> outputs/watches/orient-ra-aa0c02l19b/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Approved and delivered to `models/watches/orient-ra-aa0c02l19b.glb` |
