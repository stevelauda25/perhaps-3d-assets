# Reference plan: Seiko Prospex SPB335J1 (black coated case, black dial, rubber strap)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: delivered (round 1, 2026-11-06).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 2397 × 4120 | `front_2397x4120.jpg` | HAVE, primary for everything; taken slightly from the crown side |
| 2 | Back | none | GAP: not needed for a front relief |
| 3 | 3/4 or side | none | GAP: heights fitted to the listed 12.3 mm |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **41 mm** full case width at the widest row (listing). Checks: lug to lug 46.75 mm traced vs 46.9 listed; strap top face 19.85 mm vs 20 listed |
| Case shape | Asymmetric cushion case, wider on the crown side: left and right edges traced separately, top and bottom averaged |
| Perspective | The photo looks slightly from the crown side: the strap's side wall shows on the right, so horns and strap width come from the left edge; the strap texture is shifted by the measured 0.57 mm offset |
| Colour | Black coated case, bezel ring and crown; silver hands; mint lume; dial, insert print and strap from the photo map |
| Strap | Rubber strap with the house curl; its top face uses the photo's own strap (wave texture) |

## Parts

| Part | True shape |
| --- | --- |
| Case | Cushion case, brushed black top, rounded edge, horns either side of the strap, crown side bulges |
| Bezel | Black coin-edge ring (about 130 teeth), grey/black 60-minute insert with a lume pip at 12 |
| Dial | Black textured, sloped flange with 60 printed ticks, `SEIKO`, Prospex X, `AUTOMATIC DIVER'S 200m`, date at 4:30, small print at 6 |
| Indices | Applied black frames with mint lume: bars, wider bars at 3, 6, 9, a double plate pointed toward the centre at 12 |
| Hands | Broad baton hour and minute hands (silver, lume), black seconds hand with a lume plate and red dot |
| Crown | Large fluted black crown at about 4 o'clock (122.4 deg) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_spb335_trace   # -> config/watches/seiko-spb335j1-trace.json
python3 -B -m pipeline.seiko_spb335_dial    # -> outputs/watches/seiko-spb335j1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 52.049 px/mm from the 41 mm case width; origin = hand pivot (1169, 2060) |
| Rings | bezel teeth 19.50/18.93, insert 18.54–16.04, crystal 15.47, dial 13.26 mm |
| Horns | inner edge 10.34 mm, tips 24.0 (12) / 22.75 (6), mean 23.38 mm |
| Hands (10:12:52) | hour 303.4°, minute 69.8°, seconds 262.5° |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-spb335j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: black asymmetric cushion case, coin-edge bezel with the photo insert, black index frames with mint lume, silver baton hands, rubber strap from the photo with the 7 mm house curl |
