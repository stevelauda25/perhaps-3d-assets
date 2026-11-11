# Reference plan: Bulova 98A329 (Lunar Pilot Timascus, 43.5 mm chronograph, blue Timascus dial, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/bulova-98a329.glb`, built like `hamilton-h82405130.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, indices, numerals, hands, crown, pushers and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1225 × 2066, turned 1.9 deg clockwise | `front_1225x2066.jpg` | HAVE (original) |
| 1s | #1 turned back about the hand pivot | `front_straight_1225x2066.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 13 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 43.5 mm (22.63 px/mm) |
| --- | --- | --- |
| Case width | **43.5 mm** (anchor, Bulova) | twice the left flank's widest half from the bezel centre |
| Bezel | not listed | blue ring 41.2 mm; tachymeter ring 32.4-37.5 mm; dial 29.3 mm |
| Lug width | 20 mm | end link 20.3 mm; bracelet 19.6 / 19.9 mm next to the case |
| Lug to lug | 50 mm | 50.8 mm in the photo (tips 23.7 mm top, 27.2 mm bottom: the camera sits toward 6) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Blue anodised ring with a rounded top, black groove inside it | #1s; colour from the photo median |
| Tachymeter, minute track | Blue grained ring with white tachymeter scale; black flange with white 1/5 s ticks | dial map (prints on a grained ring) |
| Case, lugs | Cushion case wider than the bezel, short lug horns outside the end link | #1s silhouette, mean of top and bottom scaled to the listed lug to lug |
| Dial | Blue heat-treated Timascus waves; BULOVA applied plate | dial map |
| Subdials | White, snailed: 60 s at 9, 1/10 s at 3, 60 min with 262 kHz at 6 | dial map |
| Indices | Applied: polished frame around white; long and wide at 12, wide at 3 6 9, narrow bars elsewhere | #1s gridded crops |
| Numerals | Applied white 1 2 4 5 7 8 10 11 | #1s, traced by threshold with the hands cut away |
| Hands | Hour and minute: white lume batons in a polished frame, pointed tips. Chrono: white needle with a lozenge and a widening tail. Subdials: black needles, black hubs | #1s, hand-aligned crops |
| Crown | Large fluted crown at 3 (7 mm across) | #1s |
| Pushers | Blue paddle pushers at 2 and 4 | #1s outlines |
| Bracelet | Three columns, brushed; centre joints about 0.9 mm nearer the case than the outer ones | #1s |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 43.5 mm case width (Bulova); lug to lug set to the listed 50 mm |
| Photo rotation | 1.9 deg, corrected in `front_straight_1225x2066.jpg` |
| Tachymeter prints | In the dial map (white print on a grained blue ring), not traced |
| Heights | Front-relief reading of the listed 13 mm (no side photo) |
| Hand pose | The pose in #1 (about 10:07, chrono at zero) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R; pitch 5.65 mm from the first top joints |
| Dial fill | Hands and applied parts removed by copying the same row left or right (the waves run across) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_98a329_trace   # -> config/watches/bulova-98a329-trace.json
python3 -B -m pipeline.bulova_98a329_dial    # -> outputs/watches/bulova-98a329/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
