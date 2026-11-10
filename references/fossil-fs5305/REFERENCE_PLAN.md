# Reference plan: Fossil The Minimalist FS5305 (black IP steel, black dial, light brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/fossil-fs5305.glb`).
Template: the Zeppelin leather-strap builds (Z96903 frame, one photo map for dial and strap), with this watch's own parts.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2606 × 2606 | `front_2606x2606.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | `three_quarter_3000x4650.png` | HAVE, heights and part shapes only (not measured) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **44 mm** (listing, supplied by Irsyad). Check: strap 21.16 mm measured at 44 mm vs 22 mm listed (a 22 mm strap would make the case 45.7 mm) |
| Origin | Hand pivot (1280, 1304), on the fitted case circle (1279.1, 1303.4) within 1 px |
| Case | Thin black IP case, wide sloped polished bezel 18.62-22 mm, 8 mm thick listing |
| Lugs | Plain black lugs from the traced silhouette, sloped top, no step |
| Dial | Applied bar indices, FOSSIL logo, minute track with orange numerals and the orange marker at 6 stay in the dial map (flat); hands, hub and their shadows removed by a wide normalised blur fill |
| Hands | Black frames with needle tips and raised beige lume inserts (hour, minute); orange seconds needle and spear counterweight on an orange hub over a black collar. The listing says red seconds; the photo shows orange, the model follows the photo |
| Crown | Small knurled black crown at 3, radius 2.2 mm, 21.94-23.46 mm |
| Strap | Light brown leather from the front photo with the house 7 mm curl from the lug tips; the photo's strap ends at 37.5 mm, the rolled end reuses that row |

## Phase 1 outputs

```sh
python3 -B -m pipeline.fossil_fs5305_trace   # -> config/watches/fossil-fs5305-trace.json
python3 -B -m pipeline.fossil_fs5305_dial    # -> outputs/watches/fossil-fs5305/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 32.2318 px/mm from the 44 mm case circle |
| Rings | bezel inner 18.62 mm, minute track inner (flat dial edge) 16.75 mm |
| Lugs | leave the case at 16.25 mm, tips 25.75 (12) / 26.0 (6), mean 25.88 mm; outer edge 15.08 mm; strap half width 10.58 mm |
| Hands | hour 298.5°, minute 59.6°, seconds 210.8° (centre lines fitted on the lume and orange pixels) |
| Crown | 90.4°, radius 2.20 mm, 21.94-23.46 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/fossil-fs5305.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: black IP case and plain lugs, photo dial, black hands with beige lume, orange seconds, knurled crown, light brown leather strap with the 7 mm curl |
