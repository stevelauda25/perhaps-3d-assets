# Reference plan: Tissot T120.410.22.051.01 (Seastar 1000 40 mm quartz, black dial, rose gold PVD bezel and centre links)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-11.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1177 × 2012 | `front_1177x2012.jpg` | HAVE, primary for everything |
| 2 | Front, official render | `front_official_1680x1680.png` | HAVE: hand shapes (seconds counterweight, tails) |
| 3 | Side from 3 o'clock, official | `side_official_1680x1680.png` | HAVE: heights |

## Scale anchors

| Dimension | Listed | Measured at 40 mm (23.98 px/mm) |
| --- | --- | --- |
| Case width | **40 mm** (anchor, Tissot) | coin-edge bezel at 9, centred 0.05 mm from the hand pivot (547, 1021) |
| Thickness | 9.97 mm | side view 11.1 mm at its own scale; heights scaled to 9.97 |
| Lug width | 20 mm | end link 20.2 mm; bracelet tapers to 17.6 mm |
| Lug to lug | not listed | 45.5 mm (rounded lug ends) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Rose gold ring with a 120-notch coin edge; black insert with rose gold triangle, 10 20 30 40 50, bars and minute marks 1-14; polished inner lip | #1; prints traced by threshold |
| Case, lugs | Round steel case under the bezel; broad brushed lugs with rounded ends; crown guards at 3 | #1 silhouette and crops, #3 |
| Dial | Black sunray; TISSOT 1853, SEASTAR, 30 bar (300m / 1000 ft), SWISS MADE; rehaut minute track | dial map |
| Indices | Applied: rose gold frame round lume; triangle at 12, bars at 3 and 9, round dots elsewhere; date at 6 | #1 |
| Hands | Hour and minute: rose gold batons with lume and blunt points, stepped tails. Seconds: rose gold needle, lume dot at the index radius, shaft with a cross-bar counterweight | #1 profiles, #2 |
| Crown | Fluted steel crown between two crown guards | #1 |
| Bracelet | Three columns: brushed steel outer, rose gold centre links, staggered joints | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 40 mm case width (Tissot); the end link then measures 20.2 mm against 20 mm listed |
| Heights | Official side view scaled to the listed 9.97 mm |
| Hand pose | The pose in #1 (about 10:10:59) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |
| Dial under the hands | Smooth inpaint of the black sunray; the rehaut by 6 deg rotations (also replaces its reflections of the indices) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tissot_t1204102205101_trace   # -> config/watches/tissot-t120.410.22.051.01-trace.json
python3 -B -m pipeline.tissot_t1204102205101_dial    # -> outputs/watches/tissot-t120.410.22.051.01/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
