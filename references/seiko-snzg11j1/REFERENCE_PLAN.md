# Reference plan: Seiko 5 SNZG11J1 (navy dial, day-date, NATO strap)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: first build done, waiting for review.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2000 × 2966 | `front_2000x2966.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | GAP: heights estimated from the listed 13 mm thickness |
| 3 | Back | none | GAP: not needed for a front relief |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (Irsyad, 2026-11-06). Checks: lug gap 22.56 mm vs 22 mm listed; strap in the photo 23.4 mm; lug to lug 49.4 mm |
| Strap | Nylon NATO, Australian flag print from the photo, house 7 mm curl from the lug tips; keepers and buckle left out (Irsyad, 2026-11-06) |
| Case finish | Bead-blasted (matte) as in the photo: plain matte steel, no brushing lines; hands polished |
| Dial | All print in the dial map: numerals, 24 h ring, track with lume plots, logo, day-date. No applied parts |

## Parts seen

| Part | True shape |
| --- | --- |
| Case | Round, wide flat matte bezel, black gasket ring inside it; lugs wide and flat, continuous with the case |
| Dial | Navy, printed white numerals and track, triangle at 12, day-date window at 3 |
| Hands | Sword hour and minute: polished frame with a grey lume inlay, pointed tip; thin silver seconds needle, red arrowhead and red tip |
| Crown | Fluted, at 3, with a neck |
| Strap | Nylon NATO, 22 mm, printed flag, steel keepers |

Known gaps: seconds hand tail (hidden under the minute hand), heights, keepers and buckle (left out).

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snzg11_trace   # -> config/watches/seiko-snzg11j1-trace.json
python3 -B -m pipeline.seiko_snzg11_dial    # -> outputs/watches/seiko-snzg11j1/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 36.95 px/mm from the 42 mm case flanks; origin = hand pivot (941, 1399) |
| Rings | bezel inner edge 18.43 mm, dial edge 17.35 mm |
| Lug tips | 24.17 mm (12), 25.26 mm (6), mean 24.71 mm; lug gap 22.56 mm |
| Hands (10:09:35) | hour 304.5°, 8.51 mm, half width 0.83 mm; minute 58.8°, 12.94 mm, 0.72 mm; seconds 236.5°, 12.85 mm, red arrowhead 7.6–9.8 mm |

Artefacts not traced: crystal edge reflections in the gasket ring; the bottom half is about 4 % larger and 0.5 mm further right
(watch slightly turned), so means are used; the strap's right side wall shows and is cropped out of the strap atlas.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snzg11j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: matte case, sword hands with lume, NATO strap from the photo with the 7 mm curl |
| 2 | 2026-11-06 | Hand colours from the photo: bright cool white-silver frame (rougher, stays light in any viewer), cooler and darker grey lume; dark pivot dot on the hub (Irsyad) |
