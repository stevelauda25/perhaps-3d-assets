# Reference plan: Zeppelin 100 Jahre Chronograph Z76802 (7680-2: steel, black dial, black leather strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-09 (`models/watches/zeppelin-z76802.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2586 × 2586 (soft, about 30 px/mm) | `front_2586.png` | HAVE, primary for everything |
| 1b | Front turned toward the crown, 2000 × 2984 | `three_quarter_2000x2984.png` | Crown, pushers and lugs cross-check only |
| 2 | Back, side | none | GAP: heights from Z7680MB2 (same head) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: strap 21.45 mm measured; lug to lug 46.75 mm (top lugs look shorter: camera slightly off-axis) |
| Watch head | Same as Z7680MB2 (case, bezel, hand shapes, crown, pushers, heights), posed at this photo's time; bezel inner edge read from this photo (19.5 mm) |
| Origin | Hand pivot (1245, 1254); the case circle centre sits 5 px left and 4 px lower, the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z76802.glb` |
| Strap | Black leather from the front photo, each row past the lug tips stretched to the strap width; house 7 mm curl from the lug tips |
| Print, telemeter and tachymeter scales, sub-dials, lume dots, date, airship logo | Kept in the dial map; hand zones filled from the dark dial pixels only |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z76802_trace   # -> config/watches/zeppelin-z76802-trace.json
python3 -B -m pipeline.zeppelin_z76802_dial    # -> outputs/watches/zeppelin-z76802/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 29.7021 px/mm from the 42 mm case circle (left flank and the right flank clear of the crown and pushers) |
| Lugs | leave the case at 14.75 mm, tips 22.75 (12) / 24.0 (6), mean 23.375 mm; outer edge 15.1 mm; strap half width 10.72 mm |
| Hands | hour 305.6°, minute 53.8°, chronograph 0.4° |
| Crown | 90.7°, radius 3.06 mm, flutes 20.5-24.2 mm, dome to 25.4 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z76802.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: Z7680MB2 head at this photo's time, photo dial, black leather strap with the 7 mm curl |
