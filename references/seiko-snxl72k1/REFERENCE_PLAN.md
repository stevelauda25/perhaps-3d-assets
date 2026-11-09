# Reference plan: Seiko 5 SNXL72K1 (gold-tone, gold grid dial, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 2 delivered 2026-11-09.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned slightly toward the crown, 2000 × 2000 | `front_watchnation_2000.jpg` | HAVE, primary after straightening (dial about 830 px across) |
| 1b | Front, nearly straight, 900 × 900 | `front_timepiece_900.jpg` | Cross-check only |
| 2 | 3/4 from the crown side | `three_quarter_crown_2000x3004.png` | HAVE: crown, flank, bracelet profile |
| 3 | Back | `back_watchnation_2000.jpg` | HAVE (not needed for the flat-backed front asset) |

No straight-on front photo exists online (searched by SKU on 2026-11-09). In #1 the dial is 4 % narrower than tall, so
`pipeline/seiko_snxl72_rectify.py` maps the eleven lume dots to a circle (residual under 2 px) before tracing.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **37 mm** (spec sheet from Irsyad, 2026-11-09; listings agree). Cross-check: bracelet top surface 20.3 mm next to the case in #1 vs 19 mm listed lug width |
| Gold colour | Taken from the polished bezel and bracelet in the photo |
| Silhouette | Left half mirrored: the right side of #1 shows the case flank |
| SEIKO, 5 shield, lume dots | Kept in the dial map |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round polished gold bezel over a body with wide flat shoulders at 12 and 6; thick black gasket ring inside the bezel |
| Dial | Gold with a square grid of light lines every 3.1 mm, printed minute track, lume dots at the hours, applied `SEIKO` and 5 shield, `AUTOMATIC`, calibre print at 6 |
| Indices | Applied gold batons with a black inlay; wide at 12, 6 and 9; none at 3 |
| Day-date | Raised gold frame round `TUE` and `17` on white |
| Hands | Black batons with lume and a short polished base at the hub; black needle seconds hand with a long tail; black hub |
| Crown | Fluted, at about 4 o'clock |
| Bracelet | Two columns: rounded centre links half a row off the outer links, all brushed; short rows (3.8 mm) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snxl72_rectify  # -> outputs/watches/seiko-snxl72k1/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snxl72_trace    # -> config/watches/seiko-snxl72k1-trace.json
python3 -B -m pipeline.seiko_snxl72_dial     # -> outputs/watches/seiko-snxl72k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 28.85 px/mm from the 37 mm case (left flank, concentric with the crystal ring); origin = hand pivot (994, 1000) |
| Crystal ring | 15.30 mm |
| Lug tips | 20.9 mm (12), 21.6 mm (6); lug to lug 42.5 mm |
| Indices | 9.98–12.96 mm; thin 0.45 mm wide with a 0.24 mm inlay; 12, 6 and 9 1.21 mm with a 0.69 mm inlay |
| Hands | hour 306.3°, 7.61 mm; minute 50.6°, 12.29 mm; seconds 319.1°, 12.66 mm, tail 4.15 mm |
| Bracelet | pitch 3.76 mm (first rows above and below the case in #1); centre 0.432 of the half width |

The dial map fills each hand zone with the grid one or more periods (90 px) away inside the minute track, and from 6°, 12° …
away on the track.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snxl72k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: gold tone from the photo, black-inlay batons, black lume hands, gold day-date frame, two-column bracelet with the 7 mm curl |
| 2 | 2026-11-09 | Hour and minute hands end in a 90 deg point with the lume running into it (Irsyad) |
