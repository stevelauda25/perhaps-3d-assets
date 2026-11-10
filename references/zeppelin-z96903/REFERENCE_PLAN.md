# Reference plan: Zeppelin Mediterranée Z96903 (9690-3: steel, blue sunray power-reserve dial, blue leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/zeppelin-z96903.glb`).
Same model and case as [Z96905](../zeppelin-z96905/REFERENCE_PLAN.md); scripts, step and spec are copies of its files under this SKU, with white hands and gold hubs.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3996 × 6144 | `front_3996x6144.png` | HAVE, primary for everything (taken slightly from below) |
| 2 | 3/4, side, back | none | GAP: heights fitted, not measured (listing: 14 mm thick) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: strap 21.52 mm measured at 42 mm vs 22 mm listed; the other 42 mm Zeppelins measure 21.1-21.5 mm the same way |
| Origin | Hand pivot (1810, 3082); the photo is taken from below, so the case outline is not one circle: the scale comes from the flanks near the pivot row and the model keeps the case on the pivot |
| Branch, file | `main` (Irsyad 2026-11-10); `models/watches/zeppelin-z96903.glb` |
| Strap | Blue leather from the front photo with the house 7 mm curl from the lug tips |
| Lugs | Polished, stepped as on Z96905 (step at 12.29 mm); the photo shows the bottom lugs longer (perspective), the model uses the mean tip (23.5 mm) |
| Print, applied numerals, Z logo, sub-dial scales, date window, pulsometer flange | Kept in the dial map; the flange is a cone. Hands, hubs and their shadows removed from the map by a normalised blur fill |
| Hands | White, non-metallic (photo); gold centre and sub-dial hubs and seconds counterweight; red 24 h pointer with a white tail |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z96903_trace   # -> config/watches/zeppelin-z96903-trace.json
python3 -B -m pipeline.zeppelin_z96903_dial    # -> outputs/watches/zeppelin-z96903/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 76.2735 px/mm from the 42 mm case flanks |
| Rings | bezel inner 19.40 mm, flange inner (flat dial edge) 16.55 mm |
| Lugs | leave the case at 14.5 mm, tips 22.25 (12) / 24.75 (6), mean 23.5 mm; outer edge 15.58 mm; step at 12.29 mm; strap half width 10.76 mm |
| Hands | hour 300.75°, minute 29.4°, seconds 326.4° (white-pixel scan along rays from the pivot) |
| Crown | 91.5°, radius 2.53 mm, flutes 21.2-24.3 mm, dome to 25.6 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z96903.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: polished round case and stepped lugs, photo dial with the pulsometer flange as a cone, white hands with gold hubs, red 24 h pointer, fluted domed crown, blue leather strap with the 7 mm curl |
