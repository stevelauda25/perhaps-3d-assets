# Reference plan: Fossil Grant Chronograph FS4735 (polished steel, cream Roman-numeral chronograph dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 built 2026-11-10, waiting for designer review.
Template: the FS5305 leather-strap build (round case lathe, photo map for dial and strap, house curl), with this watch's own parts.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2130 × 2130 | `front_2130x2130.png` | HAVE, primary for everything |
| 2 | Slight 3/4 from the crown side | `three_quarter_2000x3016.png` | HAVE, heights and part shapes only (not measured) |
| 3 | Back | none | GAP: back is flat in the relief, not needed |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **44 mm** (listing). Check: strap 21.58 mm measured at 44 mm vs 22 mm listed (a 22 mm strap would make the case 44.85 mm) |
| Origin | Hand pivot (1039, 1065); the fitted case circle centre (1038.3, 1058.8) sits 0.24 mm higher (photo perspective) |
| Case | Polished steel round case with the wide sloped polished bezel 18.94-22 mm, 12 mm thick listing |
| Crown guard | Two shoulders above and below the crown, 2.1 mm past the case circle (right silhouette, 3.4-9.5 mm from the pivot row) |
| Lugs | Wide polished lugs from the left silhouette (the crown side shows the lug flank), sloped top |
| Dial | Roman numerals, minute track, subdial print, FOSSIL, lume squares and dial rings stay in the dial map (flat); all hands, hubs and shadows removed by a coarse plus fine normalised blur fill |
| Hands | Polished steel hour and minute frames with raised white lume; steel chronograph seconds needle with a round counterweight; three steel subdial needles at 12 with hubs |
| Pushers, crown | Round pushers at 63.5° and 118°, radius 1.0 mm, ends at 23.9-24.0 mm; large knurled crown at 3, radius 3.05 mm, 22.36-24.03 mm |
| Strap | Brown leather from the front photo with the house 7 mm curl from the lug tips; the photo's strap ends at 36.3 mm, the rolled end reuses that row |

## Phase 1 outputs

```sh
python3 -B -m pipeline.fossil_fs4735_trace   # -> config/watches/fossil-fs4735-trace.json
python3 -B -m pipeline.fossil_fs4735_dial    # -> outputs/watches/fossil-fs4735/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 25.7653 px/mm from the 44 mm case circle |
| Rings | bezel inner 18.94 mm, minute track inner (flat dial edge) 16.73 mm |
| Lugs | leave the case at 14.75 mm, tips 25.5 (12) / 26.0 (6), mean 25.75 mm; outer edge 16.55 mm; strap half width 10.79 mm |
| Hands | hour 301.5°, minute 60.4°, seconds 209.8°; subdial needles at 356-358.5° |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/fossil-fs4735.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: polished case with crown guard and pushers, photo dial, steel hands with white lume, steel chronograph and subdial needles, knurled crown, brown leather strap with the 7 mm curl |
