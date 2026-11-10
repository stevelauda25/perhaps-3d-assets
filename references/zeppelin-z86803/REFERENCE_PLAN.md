# Reference plan: Zeppelin 100 Jahre Chronograph Z86803 (8680-3: steel, cream dial, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 built 2026-11-10.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3232 × 3232 (about 43 px/mm) | `front_3232.png` | HAVE, primary for everything |
| 2 | 3/4, back, side | none | GAP: heights from Z8680MB3 / Z7680MB2 (same head) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: strap 21.46 mm measured; lug to lug 47.5 mm |
| Thickness | Listing says 13 mm; the house front relief keeps the Z7680MB2 heights (9.4 mm) before the 0.35 depth scale |
| Watch head | Same as Z8680MB3 (case, bezel, black hands with leaf and open ring, crown, pushers), posed at this photo's time; hand shapes thresholded from this photo |
| Origin | Hand pivot (1610, 1538); the case circle centre sits 13 px right and 23 px lower (camera slightly off-axis), the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z86803.glb` |
| Strap | Black leather from the front photo, each row past the lug tips stretched to the strap width; house 7 mm curl from the lug tips |
| Print, telemeter and tachymeter scales, sub-dials, applied dots, date, airship logo | Kept in the dial map; hand zones filled from the surrounding dial |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z86803_trace   # -> config/watches/zeppelin-z86803-trace.json
python3 -B -m pipeline.zeppelin_z86803_dial    # -> outputs/watches/zeppelin-z86803/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 42.9771 px/mm from the 42 mm case circle (left flank and the right flank clear of the crown and pushers) |
| Lugs | leave the case at 15.25 mm, tips 23.5 (12) / 24.0 (6), mean 23.75 mm; outer edge 14.66 mm; strap half width 10.73 mm |
| Hands | hour 304.2°, minute 54.5°, chronograph 0.2° |
| Crown | 89.7°, radius 2.44 mm, flutes 20.8-24.2 mm, dome to 25.4 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z86803.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: Z8680MB3 head at this photo's time, photo dial, black leather strap with the 7 mm curl |
