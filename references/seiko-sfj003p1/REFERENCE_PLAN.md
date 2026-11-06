# Reference plan: Seiko SFJ003P1 (Prospex Speedtimer solar 1/100 s chronograph, black dial, steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: delivered (round 1, 2026-11-06).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 3200 × 5264 | `front_3200x5264.png` | HAVE, primary for everything; taken slightly from below (inner bezel wall shows at 12, lug tips 0.85 mm low) |
| 2 | Front, official-style render, 3782 square | `front_official_3782.png` | HAVE, upscaled and soft; cross-check only (applied batons, case shape) |
| 3 | Back | none | GAP: not needed for a front relief |
| 4 | 3/4 or side | none | GAP: heights estimated for the listed 12.9 mm |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **42 mm** case width on the dial-centre row (listing). Checks: lug to lug 47.5 mm traced vs 48.3 mm listed; end links 20.25 mm between the lugs vs 20 mm listed |
| Origin | Dial centre (gasket ring; the bezel edge matches left and right). Hour and minute hands turn on the time subdial at 6, 7.25 mm below it |
| Bezel | Polished steel ring, sloped outward, 18.58 to 19.66 mm; brushed case top from there to the 21 mm edge |
| Dial | Photo map: dial, four subdials, flange print, gasket ring; all five hands removed (local lighting fill) |
| Hands | 3D: hour and minute (polished, white lume) at 9:12; white paddle hands at 0 on the 12, 9 and 3 subdials |
| Bracelet | Three columns with the house curl: outer links from the lug tips, centre links 1.9 mm further out |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round brushed body; straight shoulders from the case out to the lug corners |
| Crown and pushers | Fluted crown at 4 (121°); pushers at 2 (61°), 8 (240°), 10 (298°): stem plus grooved cap |
| Indices | Time subdial: applied polished batons filled with white lume, long at 12, 3, 6, 9. Chronograph subdials: printed |
| Hands | Polished sword hour and minute with white lume strip; white paddle hands with a narrow stem on the chronograph subdials |
| Bracelet | Three brushed columns with polished edges; centre 51 % of the width; pitch 4.64 mm; tapers 20.25 to 16.6 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_sfj003_trace   # -> config/watches/seiko-sfj003p1-trace.json
python3 -B -m pipeline.seiko_sfj003_dial    # -> outputs/watches/seiko-sfj003p1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 64.69 px/mm from the 42 mm case width; origin (1572, 2622) |
| Rings | bezel 19.66–18.58, gasket 18.09, flange inner 15.77 mm |
| Lugs | shoulders leave the case at about 9 mm (hidden by the pushers), tips 22.9 / 24.6 mm (mean 23.75) |
| Hands (9:12) | hour 275.2°, minute 87.7°, about the time-subdial pivot (0.06, -7.25) mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-sfj003p1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: round case with straight shoulders, polished bezel, photo-mapped dial with four subdials, applied batons on the time subdial, sword hour and minute hands, three white subdial hands, three pushers and a fluted crown, three-column bracelet with the 7 mm house curl |
