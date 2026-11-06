# Reference plan: Seiko 5 SNZG13K1 (black dial, day-date, steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-06 (models/watches/seiko-snzg13k1.glb).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3680 × 6400 | `front_3680x6400.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | GAP: heights from the listed 12 mm thickness (SNZG11J1 heights scaled) |
| 3 | Back | none | GAP: not needed for a front relief |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (Irsyad, 2026-11-06), not the listed 43 mm: same case as SNZG11J1; at 42 mm the lug gap reads 22.2 mm (22 mm listed), at 43 mm 22.7 mm. Lug to lug 49.0 mm |
| Bracelet | Three brushed columns from the photo, outer links from the lug tips, centre column 1.0 mm nearer the case; house 7 mm curl from the lug tips; clasp left out |
| Case finish | Satin case, bezel and crown (plain, rough 0.3); brushed lugs, end links and bracelet with the Metal009 normal map |
| Dial | All print in the dial map: numerals, 24 h ring, track, logo, day-date. No applied parts |

## Parts seen

| Part | True shape |
| --- | --- |
| Case | Round, wide flat bezel, black gasket ring inside it; lugs wide and flat, continuous with the case |
| Dial | Black, printed white numerals and track, triangle at 12, day-date window at 3 |
| Hands | Sword hour and minute: white frame with a grey lume inlay; silver seconds needle with a red arrowhead and red tip, paddle counterweight (4.3 mm, under the hour hand) |
| Crown | Fluted, at 3, against the case flank |
| Bracelet | Three columns, 21.5 mm at the lugs tapering to about 19 mm; end link of three pieces under the case |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snzg13_trace   # -> config/watches/seiko-snzg13k1-trace.json
python3 -B -m pipeline.seiko_snzg13_dial    # -> outputs/watches/seiko-snzg13k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 73.90 px/mm from the 42 mm case flanks; origin = hand pivot (1736, 3127) |
| Rings | bezel inner edge 18.70 mm, dial edge 17.16 mm |
| Lug tips | 23.54 mm (12), 25.45 mm (6), mean 24.50 mm; lug gap 22.18 mm |
| Hands (10:09:35) | hour 302.3°, 8.47 mm, half width 0.82 mm; minute 49.7°, 12.55 mm, 0.73 mm; seconds 107.0°, 12.68 mm, red arrowhead 7.9–9.7 mm |
| Bracelet | pitch 6.27 mm, centre half width 5.82 mm, centre joints 0.98 mm nearer the case |

Artefacts not traced: crystal edge reflections in the gasket ring; the bottom half is about 2 mm longer to the lug tip (watch
tilted slightly), so means are used; the far bracelet rows are foreshortened.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snzg13k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: satin case, sword hands with lume, paddle seconds tail, three-column brushed bracelet with the 7 mm curl |
