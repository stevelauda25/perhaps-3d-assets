# Reference plan: Seiko Prospex SFK001J1 (Sumo solar GMT, aqua wave dial, steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: delivered (round 2, 2026-11-06).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 2551 × 4135 | `front_2551x4135.jpg` | HAVE, primary for everything; taken slightly from the crown side and a little off-axis |
| 2 | Back | none | GAP: not needed for a front relief |
| 3 | 3/4 or side | none | GAP: heights estimated for the listed 13.2 mm |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **45 mm** full case width at the widest row (listing). Checks: lug to lug 52.25 mm traced vs 51.8 listed; bracelet between the lugs 19.97 mm vs 20 listed |
| Case shape | Symmetric: mean of the left and right edges (the right edge shows more of the case wall); top and bottom averaged |
| Centres | The photo is off-axis: dial centre, hand pivot (0.19, 0.27 mm off) and bezel centre (0.25, 0.50 mm off) all become the model origin; the insert is mapped from its own centre |
| Dial | Photo map: wave dial, 24-hour flange, date (photo shows 10, redrawn as 6 in Avenir Next Medium), prints; all four hands removed (non-blue and orange patches touching a traced hand, shadows below the hands, rotated fill, lighting only round the pivot) |
| Bezel | Polished ring with 60 rounded scallops (0.3 mm), photo insert (60-minute scale, lume pip at 12), thin polished lip at the crystal |
| Hands | 3D at 10:11 (GMT 22:12): polished hour (arrow with split lume) and sword minute hands, polished seconds with a lume ring on the tail, orange GMT arrow |
| Bracelet | Three columns with the house curl: outer links from the lug tips, centre links 2.0 mm nearer the case (photo) |

## Parts

| Part | True shape |
| --- | --- |
| Case | Sumo case: broad brushed flanks running into wide lugs, polished edges, no crown guard |
| Crown | Large fluted crown at about 3:40 (110 deg) |
| Indices | Applied polished frames with pale mint lume: round dots, wide trapezoid at 12, narrower at 6 and 9, short bar right of the date at 3 |
| Hands | Hour: broad arrow with a V-split lume and a short tail; minute: sword with a wide tail; seconds: needle with a lume ring on the counterweight; GMT: orange arrow |
| Bracelet | Three brushed columns, centre 49 % of the width, pitch about 5.6 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_sfk001_trace   # -> config/watches/seiko-sfk001j1-trace.json
python3 -B -m pipeline.seiko_sfk001_dial    # -> outputs/watches/seiko-sfk001j1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 51.82 px/mm from the 45 mm case width; origin = dial centre (1173, 2096) |
| Rings | bezel teeth 21.42/21.07, insert 20.13–15.67, crystal 15.44, flange 15.34–13.51 mm |
| Lugs | inner edge 9.99 mm, tips 26.75 (12) / 25.5 (6), mean 26.13 mm |
| Hands (10:11, GMT 22:12) | hour 305.9°, minute 64.7°, seconds 242°, GMT 333.1° |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-sfk001j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: Sumo case, polished bezel ring with the photo insert, photo-mapped wave dial and 24-hour flange, applied polished indices with lume, polished hands and orange GMT hand, fluted crown, three-column bracelet with the 7 mm house curl |
| 2 | 2026-11-06 | Date 10 → 6 (Irsyad); bezel outline scalloped again: 60 rounded lobes, 0.3 mm notches |
