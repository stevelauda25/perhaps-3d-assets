# Reference plan: Seiko 5 SNKL50K1 (gold-tone, black dial, day-date)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: first build done, waiting for review.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 4520 × 4520 | `front_4520.png` | HAVE, primary for everything (looks upscaled: small print soft) |
| 1b | Front, turned toward the crown | `front_turned_3540x4792.png` | Not traced: right flank and bracelet side visible, case outline not centred on the pivot |
| 2 | 3/4 from the crown side | `three_quarter_crown_2652.png` | HAVE: crown, case and lug height, bracelet profile |
| 3 | Back | `back_2652.png` | HAVE: display caseback, clasp, bracelet columns |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **35 mm** (Irsyad, 2026-11-06; listings say 37 and 36.5 mm). Cross-check: bracelet past the lug tips 18.36 mm at 35 mm vs 18 mm listed lug width |
| Gold colour | Taken from the polished parts in the photo; case, bracelet, indices and hands (Irsyad, 2026-11-06) |
| Front photo | Straight-on photo supplied by Irsyad on 2026-11-06 (`image 16.png`) |
| 5 shield | Kept in the dial map (gold relief on a gold plate; a traced plate would lose the 5) |

## Parts seen so far (from #1-#3)

| Part | True shape |
| --- | --- |
| Case | Round, wide polished bezel, gold |
| Dial | Black, printed minute track, `SEIKO`, applied 5 shield, `AUTOMATIC 21 JEWELS`, small print at 6 |
| Indices | Applied gold batons with a lengthwise ridge (light inner ends are reflections, not lume); double at 12; a gold square at 3 outside the day-date |
| Hands | Gold dauphine-like hour and minute with lume inserts, thin gold seconds hand with a lancet tail |
| Crown | Fluted, at about 4 o'clock |
| Bracelet | Five columns: wide brushed centre, narrow polished strips, brushed outer links; fold-over clasp with `SEIKO 5` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snkl50_trace   # -> config/watches/seiko-snkl50k1-trace.json
python3 -B -m pipeline.seiko_snkl50_dial    # -> outputs/watches/seiko-snkl50k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 59.27 px/mm from the 35 mm case flanks; origin = hand pivot (2258, 2120) |
| Crystal ring | 13.39 mm |
| Lug tips | 18.6 mm (12), 20.4 mm (6), mean 19.5 mm; lug to lug 39.0 mm |
| Indices | 8.0–12.4 mm, 0.76 mm wide (12: two bars, 1.27 mm together) |
| Hands (10:09:35) | hour 305.0°, 7.58 mm; minute 51.5°, 11.37 mm; seconds 215.3°, 12.54 mm, tail 4.46 mm |
| Bracelet | pitch 6.21 mm; centre 0.352 and strips to 0.507 of the half width, half a row off the outer links |

The dial map fills each hand zone from the same radius 6°, 12° … away (60 minute ticks); the hub and the star of hand tails take
the plain black around them; the shield's covered corner is mirrored from its other half.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snkl50k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: gold tone from the photo, faceted batons and dauphine hands, smooth 7 mm bracelet curl; 1.3 MB GLB |
| 2 | 2026-11-06 | Index inner ends gold, not lume (the light ends are reflections; Irsyad), batons 0.35 mm longer inward to cover them; `AUTOMATIC` box corrected so the A is no longer overwritten in the dial map |
