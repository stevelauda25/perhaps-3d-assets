# Reference plan: Hamilton H82405130 (Khaki Navy Scuba Auto 40 mm, black dial, red insert, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/hamilton-h82405130.glb`, built like `orient-ra-aa0818l19b.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, indices, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1840 × 3200 | `front_1840x3200.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 12.95 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 40 mm (38.24 px/mm) |
| --- | --- | --- |
| Case width | **40 mm** (anchor, listing) | coin-edge bezel and flanks at 3 and 9, centred 0.23 mm right of the hand pivot (848, 1643) |
| Bezel | not listed | rim 39.2 mm; insert 30.4-37.1 mm; inner lip 29.7 mm |
| Lug width | 20 mm (40 mm siblings) | end link 19.4 mm; bracelet 18.9 mm just past the lugs, tapering to 18.3 mm |
| Lug to lug | not listed | 47.0 mm (tips 23.6 mm top, 23.4 mm bottom) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel coin edge with about 96 rounded scallops; red aluminium insert with white triangle at 12, 20 30 40 50, bars and minute marks 1-14 | #1; prints traced by threshold, colour from the photo median |
| Case, lugs | Round case under the bezel; broad brushed lugs | #1 silhouette |
| Dial | Matte black; printed 13-24, minute track, star logo, HAMILTON, KHAKI AUTOMATIC, SWISS MADE | dial map |
| Indices | Applied: polished frame around lume; trapezoids (wide end out) at 12 3 6 9, bars elsewhere | #1; lume edges measured along rays |
| Date | White window at 4:30, date 16 | dial map |
| Hands | Hour and minute: tapered batons, polished outline, lume; short outlined tails filled black; a black slot on the minute hand's left half near the root. Seconds: black needle with a polished edge, red frame around a white lume teardrop, red pointer | #1, hand-aligned crops |
| Crown | Large fluted crown at 3, no guards | #1 |
| Bracelet | Three columns, brushed; centre links with polished chamfered ends, shorter than the outer links (4.67 mm against 5.45 mm in the photo); centre joints 1.5 mm nearer the case | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 40 mm case width (listing); the end link then measures 19.4 mm against 20 mm listed |
| Insert | One flat red (no photo map on the bezel) |
| Heights | Front-relief reading of the listed 12.95 mm (no side photo) |
| Hand pose | The pose in #1 (about 10:09:38) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Covered digits | The second 2 of 22 and the 14 are copied from the same digits elsewhere on the dial |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h82405130_trace   # -> config/watches/hamilton-h82405130-trace.json
python3 -B -m pipeline.hamilton_h82405130_dial    # -> outputs/watches/hamilton-h82405130/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
