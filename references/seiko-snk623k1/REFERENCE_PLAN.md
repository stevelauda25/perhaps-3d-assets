# Reference plan: Seiko 5 SNK623K1 (steel, black dial, applied 12 9 6, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09 (`models/watches/seiko-snk623k1.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned slightly toward the crown, 2924 × 2924 | `front_turned_2924.png` | HAVE, primary after straightening |
| 1b | Front, tilted forward, 2048 × 2048 | `front_straight_psb_2048.jpg` | Cross-check only (bracelet finish; hands cover the 9) |
| 2 | Crown side | `side_crown_monawatch_700.jpg` | HAVE: crown, flank, bracelet curve |
| 3 | Back | `back_monawatch_700.jpg` | HAVE (not needed for the flat-backed front asset) |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/seiko_snk623_rectify.py` maps the 60 white minute-track marks of #1 to one circle (median residual 0.43 px) before tracing.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **38 mm** (spec sheet from Irsyad, confirmed by Irsyad 2026-11-09; most listings say 37). Cross-checks at 38: centre link 10.41 mm vs the sheet's 10 mm "lug width"; bracelet 20.61 mm vs 18 mm listed lug width. At 37 mm the numbers would be 10.14 and 20.07 mm |
| Construction | Own case: wide lugs flow out of the case; a hood across the middle with a notch the centre column runs into; no separate end links |
| Silhouette | Left half mirrored: the right side of #1 shows the case flank and crown. Past the case it is measured from the bracelet centre (the raised bracelet sits 23 px right of the pivot) |
| SEIKO, 5 shield, print, minute track, day and date windows, applied 12 9 6 | Kept in the dial map (the windows are clean in #1; flat numeral plates rendered dark grey in model-viewer) |
| Bracelet pitch | From the first rows only: the rows further out lean away from the camera |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round bezel with a grey inner slope and a wide polished band; polished case flowing into wide lugs |
| Dial | Black, white minute track (dashes, squares at the hours), silver rehaut, `AUTOMATIC 21 JEWELS`, white date window at 3, white pill day window with red `SUNDAY` above the 6 |
| Indices | Applied steel batons with a ridge at 1, 2, 4, 5, 7, 8, 10, 11; applied polished numerals 12, 9, 6 |
| Hands | Faceted steel dauphine hour and minute with pointed tails; steel seconds needle with a counterweight bar on its tail |
| Crown | Steel, fluted, at about 4 o'clock |
| Bracelet | Two column types: wide centre links from the notch, outer links from the lug tips half a row later; brushed with polished bevels |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snk623_rectify  # -> outputs/watches/seiko-snk623k1/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snk623_trace    # -> config/watches/seiko-snk623k1-trace.json
python3 -B -m pipeline.seiko_snk623_dial     # -> outputs/watches/seiko-snk623k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 37.6428 px/mm from the 38 mm case (left flank, concentric with the crystal ring); origin = hand pivot (1443, 1438) |
| Crystal ring | 15.69 mm; black dial to 14.77 mm |
| Lugs | leave the case circle at 9.25 mm; tips 23.19 mm; lug to lug 46.38 mm; notch 19.42 mm |
| Indices | 9.59–12.805 mm, 0.877 mm wide |
| Hands | hour 303.08°, 8.275 mm; minute 53.06°, 12.731 mm; seconds 251.01°, 13.795 mm, tail 5.164 mm |
| Bracelet | pitch 6.827 mm; centre 0.505 of the half width; centre and outer rows 0.553 pitch apart |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snk623k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: all steel, applied batons (12 9 6 in the dial map), faceted dauphine hands, hood and notch, two-column bracelet with the 7 mm curl |
