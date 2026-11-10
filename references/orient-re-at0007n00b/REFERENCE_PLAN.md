# Reference plan: Orient Star RE-AT0007N00B (polished steel, grey sunburst open-heart dial, rose-gold hands, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 for review.
Method (Pasya, 2026-11-10): the front photo is cut out and projected on the whole 3D front, as the Rolex Daytona builds; the
side view stays real 3D. Template: the FS4735 leather-strap build (case, lugs, crown, house curl) with the Daytona photo materials.
File name `orient-re-at0007n00b`: the tracker matches the first word of the title (`Orient`) plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 755 × 1126 | `front_755x1126.jpg` (+ 2× working copy) | HAVE, primary for everything. GAP: under the 2000 px target, no larger official render found |
| 2 | 3/4 from the crown side | `three_quarter_738x492.webp` | HAVE, heights and part shapes only |
| 3 | Back | `back_750x750.webp` | HAVE, not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **39.3 mm** (listing). Check: strap between the lugs 20.23 / 20.26 mm measured against 20 mm |
| Origin | Hand pivot (720, 986) on the 2× copy; 34.397 px/mm |
| Photo angle | The render is taken slightly from below: case circle centre 0.9 mm below the pivot, 6 o'clock lug tips at 24.3 mm against 20.6 mm at 12. The model follows the photo outline so the projection lines up |
| Case | Round, lofted rings: flank and shoulder on the photo's case circle, wide polished bezel rising inward to the crystal ring (17.56 mm about the pivot) |
| Lugs | One slab each from the photo outline, top sloping 7.0 → 5.0 mm toward the tip |
| Dial | Flat to the minute track (14.94 mm), track cone up to the crystal ring. Open heart, power reserve, indices and numerals are print in the photo |
| Hands | Rose-gold dauphine hour and minute with tails, thin seconds needle: raised plates with the photographed hands on them (the hands stay in the dial print too) |
| Crown | Fluted, 3.24 mm radius, 19.3 → 22.7 mm along the 3 o'clock axis, 1.1 mm below the pivot (photo) |
| Strap | Black croc leather from the photo, house 7 mm curl from each side's lug tips; the clasp at 5 o'clock is left out |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_re_at0007n00b_trace   # -> config/watches/orient-re-at0007n00b-trace.json
python3 -B -m pipeline.orient_re_at0007n00b_dial    # -> outputs/watches/orient-re-at0007n00b/photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-re-at0007n00b.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: photo projected on every part, round case with the wide bezel, photo lugs, raised hands, fluted crown, black leather strap with the 7 mm curl |
