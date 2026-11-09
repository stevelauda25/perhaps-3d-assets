# Reference plan: Seiko 5 SNKL47K1 (two-tone, white dial, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 2 delivered 2026-11-09.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned slightly toward the crown, 2772 × 2772 | `front_2772.png` | HAVE, primary after straightening (looks upscaled: small print soft) |
| 1b | Front, turned the other way, 1200 × 1200 | `front_skywatches_1200.png` | Cross-check only |
| 2 | 3/4 from the crown side | `three_quarter_crown_skywatches_1200.png` | HAVE: crown, flank, bracelet profile |
| 3 | Back | `back_skywatches_1200.png` | HAVE (not needed for the flat-backed front asset) |

No straight-on front photo exists online (searched by SKU on 2026-11-09). In #1 the dial is 2.5 % narrower than tall, so
`pipeline/seiko_snkl47_rectify.py` maps the rings at the inner baton ends to a circle (residual under 3 px) before tracing.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **36.9 mm** (spec sheet from Irsyad, 2026-11-09; listings say 37 mm). Cross-check: bracelet top surface 19.5 mm next to the case vs 19 mm listed lug width |
| Colours | Steel case, bezel, lugs and bracelet; gold indices, hands, crown and bracelet strips (gold from the photo) |
| Silhouette | Left half mirrored: the right side of #1 shows the case flank, crown and clasp |
| SEIKO, 5 shield, baton rings, black square at 3 | Kept in the dial map |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, wide polished steel bezel, grey gasket line, polished lugs |
| Dial | White, printed black minute ticks, applied gold `SEIKO` and 5 shield, `AUTOMATIC 21 JEWELS`, calibre print at 6, printed black square at 3 |
| Indices | Applied gold batons with a ridge and a small grey ring at the inner end; none at 3 |
| Day-date | Thin raised steel frame round `TUE` and `23` |
| Hands | Gold dauphine hour and minute with a cream lume strip and short pointed tails; gold seconds needle with a wide counterweight bar |
| Crown | Gold, fluted, at about 4 o'clock |
| Bracelet | Three columns: brushed steel centre, polished gold strips, brushed steel outer links half a row off; end links split the same way |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snkl47_rectify  # -> outputs/watches/seiko-snkl47k1/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snkl47_trace    # -> config/watches/seiko-snkl47k1-trace.json
python3 -B -m pipeline.seiko_snkl47_dial     # -> outputs/watches/seiko-snkl47k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 32.33 px/mm from the 36.9 mm case (left flank, concentric with the crystal ring); origin = hand pivot (1379, 1387) |
| Crystal ring | 14.81 mm |
| Lug tips | 21.1 mm; lug to lug 42.3 mm |
| Indices | 8.80–13.41 mm, 0.80 mm wide |
| Hands | hour 305.0°, 8.08 mm; minute 54.3°, 12.23 mm; seconds 359.9°, 13.27 mm, counterweight 4.89 mm |
| Bracelet | pitch 5.13 mm; centre 0.356 and gold strips to 0.484 of the half width |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snkl47k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: two-tone (steel with gold indices, hands, crown and strips), gold dauphine hands, thin steel day-date frame, three-column bracelet with the 7 mm curl |
| 2 | 2026-11-09 | SEIKO and the 5 shield whole (seconds needle inpainted out of the logo); TUE and 23 redrawn as clean type in the dial map (Irsyad) |
