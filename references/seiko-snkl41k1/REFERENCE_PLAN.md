# Reference plan: Seiko 5 SNKL41K1 (steel, white dial, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 2 built 2026-11-09, waiting for the designer.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned and tilted, 2000 × 3416 | `front_2000x3416.png` | HAVE, primary after straightening |
| 1b | Straight front, 800 × 800 | `front_straight_jamtangan_800.jpg` | Cross-check only (too small to trace) |
| 1c | Front, turned the other way, 1000 × 1000 | `front_watchspree_1000.jpg` | Cross-check only |
| 2 | Crown side | `side_crown_jamtangan_800.jpg` | HAVE: crown, flank, bracelet curve |
| 3 | Back | `back_jamtangan_800.jpg` | HAVE (not needed for the flat-backed front asset) |

The only straight-on photo online is 800 px. `pipeline/seiko_snkl41_rectify.py` maps the 46 printed minute ticks of #1 to
one circle (median residual 0.33 px) before tracing.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **37 mm** (spec sheet from Irsyad, 2026-11-09). Cross-check: bracelet 17.44 mm past the lug tips vs 18 mm listed lug width |
| Construction | Same case, dial and bracelet as SNKL47K1, all steel: the SNKL47K1 build step runs with this spec |
| Silhouette | Left half mirrored: the right side of #1 shows the case flank, crown and clasp |
| SEIKO, 5 shield, index ends, black square at 3 | Kept in the dial map |
| Bracelet pitch | From the top rows only: the lower rows lean away from the camera |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, wide polished steel bezel, grey gasket line, polished lugs |
| Dial | White, printed black minute ticks, applied steel `SEIKO` and 5 shield, `AUTOMATIC 21 JEWELS`, calibre print at 6, printed black square at 3 |
| Indices | Applied steel batons with a ridge and a rounded, dark-outlined inner end; none at 3 |
| Day-date | Thin raised steel frame round `MON` and `9` |
| Hands | Steel dauphine hour and minute with a lume strip and pointed tails; steel seconds needle with a wide counterweight bar |
| Crown | Steel, fluted, at about 4 o'clock |
| Bracelet | Three columns: brushed centre, polished strips, brushed outer links half a row off; end links split the same way |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snkl41_rectify  # -> outputs/watches/seiko-snkl41k1/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snkl41_trace    # -> config/watches/seiko-snkl41k1-trace.json
python3 -B -m pipeline.seiko_snkl41_dial     # -> outputs/watches/seiko-snkl41k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 45.8197 px/mm from the 37 mm case (left flank, concentric with the crystal ring); origin = hand pivot (1194, 1197) |
| Crystal ring | 15.042 mm |
| Lug tips | 21.375 mm; lug to lug 42.75 mm |
| Indices | 8.73–13.575 mm, 0.808 mm wide |
| Hands | hour 305.51°, 7.213 mm; minute 51.96°, 12.36 mm; seconds 304.19°, 12.506 mm, counterweight 4.903 mm |
| Bracelet | pitch 4.801 mm; centre 0.409 and strips to 0.517 of the half width |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snkl41k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: all steel, dauphine hands with lume, thin steel day-date frame (MON 9 redrawn as clean type), three-column bracelet with the 7 mm curl |
| 2 | 2026-11-09 | SEIKO and the 5 shield darkened in the dial map (x2 against the dial); white lume strip raised above the hand ridge so it shows (Irsyad) |
