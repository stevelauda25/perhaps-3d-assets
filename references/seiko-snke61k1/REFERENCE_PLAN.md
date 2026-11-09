# Reference plan: Seiko 5 SNKE61K1 (steel, navy dial, lume batons, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09 (`models/watches/seiko-snke61k1.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned toward the crown (3/4), 2048 × 2048 | `front_turned_2048.png` | HAVE, primary after straightening |
| 1b | Near-front, 2772 × 2772 (upscaled, soft) | `front_near_2772.png` | Cross-check (bracelet) and dial-map patches |
| 2 | Crown side | #1 shows the crown and flank | Enough for the front asset |
| 3 | Back | none | Not needed for the flat-backed front asset |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/seiko_snke61_rectify.py` maps the 60 minute-track marks of #1 (48 dashes and the dots at the 5-minute numerals) to one circle (median residual 2.1 px), then registers #1b onto the same frame with SIFT matches on the dial (43 inliers, median 0.7 px).

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **38 mm** (Irsyad's spec sheet, 2026-11-09). Check at 38: bracelet between the lugs 19.26 mm vs 18 mm listed lug width (same pattern as SNK623K1). At 18 mm the case would be 35.5 mm |
| Origin | Minute-track centre. The raised hands sit 0.63 mm left of it in the 3/4 photo (parallax); the model puts them on the centre |
| Construction | Own case: short brushed lugs outside the bracelet; three-column end link from under the case to the lug tips; no hood |
| Silhouette | Left half mirrored: the right side of #1 shows the case flank and crown |
| SEIKO, 5 shield, printed lume 12 9 6, print, minute track, day-date window | Kept in the dial map; where the seconds hand crosses SEIKO, the 5 shield and the print they are patched from #1b, colour-matched per channel |
| Bracelet pitch | 7.0 mm for both columns: the first rows read 6.4-6.8 mm (centre) and 7.5-8.1 mm (outer) because they lean away from the camera |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round bezel with a grey inner slope and a wide sloping polished band; polished case |
| Dial | Navy, white minute track with numerals 5-60, grey rehaut, printed lume 12 9 6, applied SEIKO and 5 shield, `AUTOMATIC 21 JEWELS`, day-date window with a steel frame at 3 |
| Indices | Applied steel batons with a lume insert at 1, 2, 4, 5, 7, 8, 10, 11 |
| Hands | Steel leaf hour and minute hands, widest near the middle, lume insert; steel seconds needle with an orange tip and a lume disc on the tail |
| Crown | Steel, fluted, at about 3:40 |
| Bracelet | Three columns: outer links from the lug tips, centre links half a row later; brushed with polished bevels |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snke61_rectify  # -> outputs/watches/seiko-snke61k1/front_rectified.png, front_near_registered.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snke61_trace    # -> config/watches/seiko-snke61k1-trace.json
python3 -B -m pipeline.seiko_snke61_dial     # -> outputs/watches/seiko-snke61k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 26.9942 px/mm from the 38 mm case (left flank, concentric with the crystal ring); origin = dial centre (1050, 1050) |
| Crystal ring | 15.345 mm; navy dial to 13.78 mm |
| Lugs | leave the case circle at about 12 mm; tips 21.89 mm; lug to lug 43.79 mm |
| Indices | 8.39-11.56 mm, 0.63 mm wide |
| Hands | hour 303.38°, 7.675 mm; minute 54.32°, 11.812 mm; seconds 163.16°, 11.766 mm, tail 6.326 mm with a 0.59 mm disc |
| Bracelet | 19.26 mm wide; centre 0.477 of the half width (9.19 mm); first centre joint 26.88 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snke61k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: all steel, lume batons and leaf hands, seconds with a lume disc, short lugs and a three-column end link, three-column bracelet with the 7 mm curl |
