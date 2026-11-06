# Reference plan: Seiko Presage Classic SPB467J1 (salmon stucco dial, 6R55, seven-column steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photos supplied by Irsyad on 2026-11-06.

## Target asset

A front-facing GLB in `models/watches/seiko-spb467j1.glb`, built like the other Seiko front reliefs: flat back, 2.5D depth, case/bezel/indices/hands/bracelet as geometry, dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, nearly straight-on, transparent background, 2204 × 2204 | `front_2204.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | `three_quarter_5684x8576.png` | HAVE: case flank, crown, bracelet columns |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Value | Measured at 40.2 mm (30.85 px/mm) |
| --- | --- | --- |
| Case diameter | **40.2 mm** (anchor, Irsyad) | case edge left of and below the hand pivot (1040, 1028) |
| Lug width | 20 mm listed | bracelet face 20.3 mm next to the lug tips (the silhouette, 21.2 mm, includes the right side wall) |
| Lug to lug | not checked | 45.5 mm (tips 22.4 mm at 12, 23.1 mm at 6) |
| Bezel, crystal, dial flat | not listed | 19.18, 17.60, 15.21 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, polished, wide sloped bezel down to a box crystal | #1, #2 |
| Lugs | Long polished lugs flowing from the case flank | #1 silhouette |
| Dial | Salmon stucco (random texture), sloped flange with 60 ticks and fine rings | dial map |
| Indices | Applied polished batons 10.5–15.1 mm; double at 12; short at 3 (14.1–15.6 mm) beside the date | #1 |
| Date | Window at 3 with a polished frame, black digit on white | frame geometry, digit in the map |
| Print | `SEIKO`, `PRESAGE AUTOMATIC 3 DAYS`, `JAPAN 6R55 …` | dial map |
| Hands | Faceted dauphine hour and minute; thin seconds needle with a long narrow counterweight; hub boss | #1 |
| Crown | Big fluted crown with a plain domed cap at 3 | #1, #2 |
| Bracelet | Seven columns: brushed outer links and middle links B, D in one row; polished pills A, C, E half a row out of step (1.9 mm nearer the case); pitch 5.0 mm | #1, #2 |
| End link | Between the lugs from under the case: outer, B, D to the lug tips; pill columns 1.9 mm shorter | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 40.2 mm case (Irsyad, 2026-11-06) |
| Heights | Estimated for a 12 mm case with a box crystal (no side measurement) |
| Hand pose | The pose in #1 (10:08:42) so the comparison render lines up |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 15.4 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_spb467_trace   # -> config/watches/seiko-spb467j1-trace.json
python3 -B -m pipeline.seiko_spb467_dial    # -> outputs/watches/seiko-spb467j1/dial_photo.jpg (regenerated, not committed)
```

The dial map fills each hand zone with the lighting from around the hand and detail rotated 6°, 12° … (60 flange ticks; the stucco is random). Around the hub (2.6 mm) the detail comes from a clean patch at (5.2, −3.0) mm.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-spb467j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: seven-column bracelet with the house curl, house depth, glass and steel |

## Known gaps and artefacts

- The photo is turned slightly: the right side walls of the bracelet and case show; the build is symmetric.
- A small pale patch in the dial map at the minute-hand tip on the flange (2 o'clock).
- Case and crystal heights are estimates.
