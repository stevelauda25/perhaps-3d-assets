# Reference plan: Orient FAA02004B9 (Ray II, black dial, black bezel insert, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.
House method: modelled case, crown guards, bezel ring, indices, hands, crown and bracelet in house steel and glass; one photo map
for the dial print, the day-date wheels and the bezel insert print.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1811 × 2956 | `front_1811x2956.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 13 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 41.5 mm (35.69 px/mm) |
| --- | --- | --- |
| Bezel | **41.5 mm** (anchor, listing) | centre from the insert's outer edge (0.14 mm below the hand pivot), radius at 9 o'clock |
| Lug width | 22 mm | end link 21.3 mm; bracelet 21.4 mm just past the lugs (perspective: the bracelet sits lower than the bezel) |
| Lug to lug | 47 mm | 46.0 mm (tips 22.6 mm top, 23.4 mm bottom) |
| Bezel rings | not listed | crystal 30.8 mm, black insert 32.1-37.9 mm, steel ring to 41.5 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round under the bezel; crown guards at 3 | #1 silhouette and gridded crop |
| Bezel | Polished steel ring with about 60 half-moon recesses; black insert with white print (triangle with dot, minute bars 1-14, 10-50) | #1; insert from the photo map |
| Dial | Glossy black, printed minute track on a sloped chapter ring, crown emblem, ORIENT, Automatic, Water Resist 200m, movement print | dial map |
| Indices | Applied polished frames with lume: dots, trapezoid at 12, tapered bars at 6 and 9; polished day-date frame with a divider | #1, rotated crops |
| Hands | Hour: polished frame, black inside, arrow-head lume over a smaller lume block, needle tip; minute: sword with lume blade; seconds: polished needle, hollow red arrow | #1, rotated crops (half-width profiles) |
| Crown | Fluted, between the crown guards | #1 |
| Bracelet | Three columns, brushed; centre links with polished edge strips; centre joints 2.1 mm nearer the case; pitch 5.9 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 41.5 mm bezel (listing, Orient USA) |
| Bezel insert | Photo map on a modelled ring (like SRPG18J1), not projected on the steel |
| Heights | Front-relief reading of the listed 13 mm (no side photo) |
| Hand pose | The pose in #1 so the comparison render lines up |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_faa02004b9_trace   # -> config/watches/orient-faa02004b9-trace.json
python3 -B -m pipeline.orient_faa02004b9_dial    # -> outputs/watches/orient-faa02004b9/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Approved and delivered to `models/watches/orient-faa02004b9.glb` |
