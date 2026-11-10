# Reference plan: Fossil Carraway FS6012 (steel rectangular case, cream Roman-numeral dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/fossil-fs6012.glb`).
First Fossil. Scripts follow the Zeppelin Z96903 files (photo map for dial and strap, house curl); the rectangular case is its own construction.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2802 × 5774 (half of the 5604 × 11548 original) | `front_2802x5774.png` | HAVE, primary for everything (taken slightly from below) |
| 2 | 3/4, side, back | none | GAP: heights fitted, not measured (listing: 9.6 mm thick) |
| 3 | Spec sheets | `spec_sheet.png`, `spec_sheet_2.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | **30 mm** listed "case diameter" read as the case width without the crown. Check: strap 22.28 mm measured (left edge × 2) and 22.63 mm between the brancards vs 22 mm listed |
| Origin | Hand pivot (1310, 2906) of the working copy |
| Branch, file | `main` (same as Zeppelin); `models/watches/fossil-fs6012.glb` |
| Case | Lower outer flank (silhouette to the step at 13.51 mm), raised brushed brancards (step to 11.32 mm) that run up into the horns, one polished slab for top bar, frame and bottom bar with the dial opening as a hole |
| Strap | Brown leather from the front photo with the house 7 mm curl from the mean horn tip (20.62 mm) |
| Print, numerals, minute track, FOSSIL, raised centre panel | Kept in the dial map (flat). Hands, hub and their shadows removed from the map by a normalised blur fill |
| Hands | Black lozenge hour and minute hands with raised lume inserts; black seconds needle with a long counterweight tail; black hub, steel pin |

## Phase 1 outputs

```sh
python3 -B -m pipeline.fossil_fs6012_trace   # -> config/watches/fossil-fs6012-trace.json
python3 -B -m pipeline.fossil_fs6012_dial    # -> outputs/watches/fossil-fs6012/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 71.2667 px/mm from the 30 mm flanks |
| Case | flank to ±15.0 mm, step 13.51 mm, brancard inner 11.32 mm; horn tips 20.25 (12) / 21.0 (6); flank ends 17.5 / 18.5 |
| Bars, dial | top bar 17.23 to 14.33 mm, bottom bar -14.30 to -17.81 mm; dial opening x -10.45..10.31, y 13.20..-13.46 mm |
| Hands | hour 305.2°, minute 57.6°, seconds 155.1° with the tail at 335.1° |
| Crown | 91.1°, radius 3.16 mm, neck 15.08-15.86, flutes to 17.33, rounded end to 17.85 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/fossil-fs6012.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: rectangular case with flank, brushed brancards and polished bars, photo dial, black lume hands, fluted crown, brown leather strap with the 7 mm curl |
