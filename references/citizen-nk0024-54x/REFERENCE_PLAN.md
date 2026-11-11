# Reference plan: Citizen NK0024-54X (Tsuyosa 60 automatic, 40 mm, green patterned dial, gold-tone bezel, two-tone bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-11.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 960 × 1769 | `front_960x1769.jpg` | HAVE, primary for everything |
| 2 | Front, official render | `front_official_1200x2048.png` | HAVE, cross-check |
| 3 | Side, official | `side_official_1424x2048.png` | HAVE: heights, crown at 4, cyclops |
| 4 | Back, official | `back_official_1553x2048.png` | HAVE, not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 40 mm (19.9 px/mm) |
| --- | --- | --- |
| Case width | **40 mm** (anchor, Citizen) | widest steel row at 3 and 9 |
| Thickness | 10.9 mm | side view 12.9 mm at its own scale; heights scaled to 10.9 |
| Bracelet | not listed | 21.6 mm at the case, tapering to 20.6 mm |
| Case to case | not listed | 44.75 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Brushed steel body, round round the bezel, tapering into the bracelet; lower end pieces past a horizontal edge at 12 and 6 | #1 silhouette, #3 |
| Bezel | Smooth domed gold-tone ring; gold rehaut inside | #1 radial profiles, #3 |
| Dial | Green, a 3 deg radial pattern (120 cells) with concentric rings at the centre; CITIZEN, AUTOMATIC, printed minute track with squares at the hours; date at 3 | dial map |
| Indices | Applied gold-framed lume bars, pairs at 12 and 6 | #1 by threshold, one rectangle each |
| Cyclops | Rounded rectangular lens over the date | #1, #3 |
| Hands | Gold batons with lume and square ends, stub tails; gold seconds needle with a thin tail | #1 colour profiles |
| Crown | Fluted gold crown at 4, no guards | #1, #3 |
| Bracelet | Five columns: brushed steel outer, polished gold semi and centre links, centre row half a link off | #1 brightness dips |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 40 mm case width (Citizen) |
| Origin | The dial centre (pattern and index ring); the hand stack shows 0.25 mm higher in the photo (parallax) and is placed on the centre |
| Heights | Official side view scaled to the listed 10.9 mm |
| Hand pose | The pose in #1 (about 10:07:37) |
| Bracelet curve | House curl: 7 mm radius from the case tips, end_y = tip + 2.2 R |
| Dial under the hands | Pattern copied by whole 6 deg turns over the local lighting; the hub zone mirrors the rings just outside it |

## Phase 1 outputs

```sh
python3 -B -m pipeline.citizen_nk0024_trace   # -> config/watches/citizen-nk0024-54x-trace.json
python3 -B -m pipeline.citizen_nk0024_dial    # -> outputs/watches/citizen-nk0024-54x/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
