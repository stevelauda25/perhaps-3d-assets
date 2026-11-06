# Reference plan: Seiko 5 Sports SNZ450J1 (gold-tone, gold dial, day-date)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: first build done, waiting for review.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2510 × 2492 | `front_2510.png` | HAVE, primary for everything (soft: small print and minute numerals blurred) |
| 1b | Front, turned toward the crown | `front_turned_1350x2450.png` | Not traced: second check for the dial print and bezel claws |
| 2 | 3/4 from the crown side | `three_quarter_crown_2168.png` | HAVE: crown, case and bezel height, bracelet profile |
| 3 | Back | `back_2400.png` | HAVE: display caseback, clasp, bracelet columns |

## Scale (front photo)

| Item | Pixels | At 38 mm |
| --- | --- | --- |
| Case width on the flanks, crown excluded (x 578 to 1876 at y 1180) | 1298 | 34.2 px/mm |
| Bracelet width above and below the case (y 240 and 2300) | 572 | 16.7 mm |
| Hand pivot (first read) | (1228, 1115) | |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **38 mm** across the flanks (Irsyad, 2026-11-06; listings say 38 mm). Bracelet past the first link 16.25 mm (no lug width listed) |
| Gold colour | Same gold as SNKL50K1 (the photo's mid-tones match it) |
| Applied logo | SEIKO and the 5 shield are gold on gold and too soft to trace here: SEIKO from the SNKL50K1 photo, shield from the SNK607K1 trace, fitted by width to this photo's logo boxes |
| Photo turn | The photo is turned about 2 deg (indices) and tilted (hub 10 px above the index circle centre): the dial UV turns it back, no resampling |
| Case outline | Traced r(angle), upper half mirrored to the 6 side (the 6 side shows more end link from the tilt); flat edge at 12 and 6 |
| Bracelet facets | The triangular facets on the outer links are not modelled in round 1 (plain boxes with the curl) |

## Parts seen (from #1-#3)

| Part | True shape |
| --- | --- |
| Case | Not round: sculpted, polished gold; scalloped outer edge with four pointed claws (about 1:30, 4:30, 7:30, 10:30) and teardrop scoops at 12, 3, 6 and 9; crown-guard bulge at 3 |
| Bezel | Wide polished ring round the crystal, its outer edge following the scallops |
| Dial | Gold sunburst; printed minute track with 05-55 numerals; printed date track 2-19 on a black arc from 1 to 5 o'clock; applied `SEIKO` and 5 shield; `SPORTS`, `WATER 100M RESIST`, `AUTOMATIC`, `23 JEWELS`; small print at 6 |
| Indices | Applied gold batons with white lume; pointed shield-shaped marker at 12; none at 3 (day-date) |
| Day-date | White window, `WED 30`, gold frame |
| Hands | Gold baton hour and minute with white lume and black edges; thin gold seconds hand with an arrow tip and tail |
| Crown | Fluted, at 3, gold |
| Bracelet | Three columns: polished centre links half a row off the brushed outer links; outer links carry pointed triangular facets ("X" pattern); fold-over clasp with `SEIKO` (rolled under, not seen from the front) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snz450_trace   # -> config/watches/seiko-snz450j1-trace.json
python3 -B -m pipeline.seiko_snz450_dial    # -> outputs/watches/seiko-snz450j1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 34.16 px/mm from the 38 mm case flanks; origin = circle through the index lume (1231, 1116); hub (1230, 1106) |
| Crystal ring / bezel | 12.33 mm / 13.41 mm |
| Case | flat edge at 12 and 6: 16.86 mm; flanks 19.0 mm; four corner claws and two side claws, dishes at 12, 6 and on the flanks |
| Indices | lume 9.41–11.85 mm, 0.86 mm wide, in 0.15 mm gold frames; pentagon at 12, 8.20–11.83 mm, 1.93 mm wide |
| Hands (10:11:19) | hour 305.9°, 7.93 mm; minute 69.1°, 11.64 mm; seconds 113.5°, 11.56 mm, tail 6.0 mm |
| Bracelet | first outer joint (bend start) 19.76 mm; pitch 7.39 mm; centre column 0.45 of the half width, joints 0.376 row past the outer ones |

The dial map fills each hand zone from the same radius 6°–30° away (60 minute ticks); within 3 mm of the hub only the lighting
is kept (turned copies draw a fan there). Copies over the date track can repeat a digit under the minute hand.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snz450j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: sculpted gold case (dishes and claws on the traced outline), polished bezel, white-lume batons, baton hands with black inlays, smooth 7 mm bracelet curl; 1.3 MB GLB |
| 2 | 2026-11-06 | SEIKO and 5 shield as raised polished plates (were faint in the dial map; Irsyad): SEIKO traced from the SNKL50K1 photo, shield from the SNK607K1 trace, both fitted to this photo's logo outline |
