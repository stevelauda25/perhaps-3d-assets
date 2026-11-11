# Reference plan: Tissot T120.607.11.041.00 (Seastar 2000 Professional 46 mm, blue wave dial, ceramic insert, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/tissot-t120.607.11.041.00.glb`, built like `hamilton-h82405130.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, indices, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2208 × 3262 | `front_2208x3262.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 15.8 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 46 mm (41.53 px/mm) |
| --- | --- | --- |
| Case width | **46 mm** (anchor, listing) | coin-edge bezel at 3 and 9, centred 0.1 mm right of / below the hand pivot (1013, 1603) |
| Bezel | not listed | insert 35.5-43.4 mm; inner lip 33.6 mm; coin edge from 44.2 mm |
| Lug width | 22 mm | end link 21.9 mm; bracelet 21.0 mm just past the lugs, tapering to 19.1 mm |
| Lug to lug | not listed | 49.5 mm (tips 24.6 mm top, 24.9 mm bottom) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel ring with a coin edge (90 notches); dark polished ceramic insert with white triangle at 12, 20 30 40 50, bars and minute marks 1-14; polished inner lip | #1; prints traced by threshold, colour from the photo median |
| Case, lugs | Round case under the bezel; broad brushed lugs; polished crown guards at 3 | #1 silhouette and crops |
| Dial | Blue gradient with wave relief; black flange with minute track; TISSOT 1853, SEASTAR, PROFESSIONAL 600M / 2000FT, POWERMATIC 80, SWISS MADE | dial map |
| Indices | Applied: polished frame around lume; triangle at 12, bars at 3, 9 and 6, round dots elsewhere | #1; dots by threshold (the dot at 2 is placed on the mean radius) |
| Date | Window at 6 with a polished frame, date 31 | dial map |
| Hands | Hour: sword with lume blade, black cross guard, black grip and a stepped pommel. Minute: baton with an arrow tip, lume, stepped black tail. Seconds: black needle, lume dot in a polished ring, outlined tip | #1, hand-aligned crops |
| Crown | Large fluted crown at 3 between two crown guards | #1 |
| Bracelet | Three columns, brushed, staggered joints | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 46 mm case width (listing); the end link then measures 21.9 mm against 22 mm listed |
| Insert | One flat dark ceramic colour (no photo map on the bezel) |
| Heights | Front-relief reading of the listed 15.8 mm (no side photo) |
| Hand pose | The pose in #1 (about 10:10:39) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Dial under the hands | Smooth inpaint of the blue dial (the wave relief does not repeat; every filled pixel lies under a 3D hand or index); the flange is filled by 6 deg rotations |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tissot_t120607_trace   # -> config/watches/tissot-t120.607.11.041.00-trace.json
python3 -B -m pipeline.tissot_t120607_dial    # -> outputs/watches/tissot-t120.607.11.041.00/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
