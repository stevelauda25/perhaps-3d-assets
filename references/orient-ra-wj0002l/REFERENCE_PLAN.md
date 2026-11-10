# Reference plan: Orient RA-WJ0002L (Mako 40 Solar, blue sunburst dial, khaki bezel, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.
House method: modelled case, bezel rim, indices, numerals, hands, crown and bracelet in house steel and glass; one photo map for
the dial print and the bezel insert print.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1884 × 3235 | `front_1884x3235.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 13 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 39.9 mm (37.88 px/mm) |
| --- | --- | --- |
| Case | **39.9 mm** (anchor, listing) | circle on the case flanks, centred 0.2 mm from the hand pivot |
| Lug width | 20 mm | end link 19.5 mm; bracelet 19.6 mm just past the lugs (perspective: the bracelet sits lower than the case) |
| Lug to lug | 46.5 mm | 45.75 mm (tips 22.6 mm top, 23.1 mm bottom) |
| Bezel rings | not listed | crystal 30.6 mm, khaki insert 30.9-37.5 mm, coin-edge rim to 38.3 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, its polished flank shows outside the bezel; small notches at 9 and beside the lugs | #1 silhouette |
| Bezel | Polished coin-edge rim with about 60 round dimples; khaki insert with white print (triangle, minute dots 1-14, bars, 10-50) | #1; insert from the photo map |
| Dial | Blue sunburst, printed minute track, crown emblem, ORIENT, solar-powered, Water Resistant 20 bar, movement print | dial map |
| Indices | Applied polished frames with lume at 1 2 4 5 7 8 10 11; applied polished 12, 9, 6; polished date frame at 3 | #1, numerals traced by threshold |
| Hands | Hour and minute: polished frame, black inside, lume inlay, pointed; seconds: polished needle, orange bulb and tip, dark counterweight | #1, rotated crops |
| Crown | Fluted crown with a smooth collar at 3 | #1 |
| Bracelet | Three columns, brushed; centre joints 1.5 mm nearer the case; pitch 6.4 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 39.9 mm case (listing), same reading as the sibling RA-WJ0004Y |
| Bezel insert | Photo map on a modelled ring (like SRPG18J1), not projected on the steel |
| Heights | Front-relief reading of the listed 13 mm (no side photo) |
| Hand pose | The pose in #1 so the comparison render lines up |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_wj0002l_trace   # -> config/watches/orient-ra-wj0002l-trace.json
python3 -B -m pipeline.orient_ra_wj0002l_dial    # -> outputs/watches/orient-ra-wj0002l/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Approved and delivered to `models/watches/orient-ra-wj0002l.glb` |
