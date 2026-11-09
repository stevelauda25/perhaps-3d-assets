# Reference plan: Seiko 5 SNKK22K1 (gold-tone, black dial, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1920 × 1920 | `front_1920.png` | HAVE, primary for everything (below the 2000 px target: dial about 800 px across, small print soft) |
| 1b | Front, turned toward the crown | `front_turned_3680x6400.png` | Not traced: turned, looks upscaled |
| 2 | 3/4 from the crown side | none | MISSING: heights taken from SNK607K1/SNKL50K1 (same case family) |
| 3 | Back | none | MISSING: not needed for the flat-backed front asset |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **38 mm** (spec sheet from Irsyad, 2026-11-09; PSB Watches lists 37 mm). Cross-check: bracelet top surface 18.9 mm at the first row vs 18 mm listed lug width (+5 %); silhouette with the visible right flank 20.74 mm |
| Gold colour | Taken from the polished bezel and bracelet in the photo |
| SEIKO and 5 shield | Kept in the dial map (gold relief on a black dial) |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, wide polished gold bezel, thin dark gasket line, gold rehaut inside it |
| Dial | Black with a faint inner disc, white minute ticks, applied `SEIKO` and 5 shield, `AUTOMATIC 21 JEWELS`, `MADE IN JAPAN` and calibre print at 6 |
| Indices | Applied polished gold frames with a cream lume insert; wide at 6 and 9; two bars at 12; none at 3 |
| Day-date | Raised gold frame round `SUN` (red) and `5` on white |
| Hands | Straight gold batons with lume and broad square tails (a cross round the hub); thin gold needle seconds hand with a plain tail |
| Crown | Fluted, at about 4 o'clock |
| Bracelet | Three columns: brushed centre, narrow polished strips, brushed outer links half a row off |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snkk22_trace   # -> config/watches/seiko-snkk22k1-trace.json
python3 -B -m pipeline.seiko_snkk22_dial    # -> outputs/watches/seiko-snkk22k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 26.52 px/mm from the 38 mm case flanks; origin = hand pivot (922, 892) |
| Crystal ring | 15.03 mm (gasket line); dial black to 13.65 mm, gold rehaut between |
| Lug tips | 21.6 mm (both ends); lug to lug 43.3 mm |
| Indices | 9.18–12.57 mm; single 1.16 mm wide, lume 0.51 mm; 6 and 9 2.11 mm; 12 two bars 2.53 mm together |
| Hands | hour 307.0°, 8.21 mm; minute 52.4°, 11.80 mm; seconds 252.4°, 11.83 mm, tail 3.86 mm |
| Bracelet | pitch 6.28 mm (mean of the first rows above and below, foreshortened differently); centre 0.36 and strips to 0.508 of the half width |

The dial map fills each hand zone from the same radius 6°, 12° … away (60 minute ticks); the hub ring takes the plain black
around it; the hands' glow is never used as a source.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snkk22k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: gold tone from the photo, framed lume indices, baton hands, gold day-date frame, smooth 7 mm bracelet curl |
