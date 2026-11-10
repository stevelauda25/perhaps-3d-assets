# Reference plan: Emporio Armani Matteo AR11328 (blue anodised case, green-to-black dial, blue Milanese mesh)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/emporio-armani-ar11328.glb`).
Template: the Fossil FS5305 three-hand build (round case lathe, photo dial, house curl) with the Zeppelin Z8680M4 mesh map; lug arms and end caps are this watch's own construction.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 4442 × 4442 | `front_4442x4442.png` | HAVE, primary for everything; soft (about 4x upscaled), so parts are read from gridded crops |
| 2 | 3/4 from the crown side | `three_quarter_2718x3600.png` | HAVE, heights and part shapes only (not measured) |
| 3 | Back | none | GAP: back is flat in the relief, not needed |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **43 mm** (listing). Check: end cap 19.63 mm measured vs 20 mm listed; the mesh itself is 17.63 mm |
| Origin | Hand pivot (2150, 2218); the fitted case circle centre sits 0.34 mm right of it (photo perspective toward the crown) |
| Case | Matte blue anodised round case, straight flank into a wide domed bezel, crystal opening 17.39 mm, flat back cover, 10 mm thick listing |
| Lugs | Open arms: outer edge from the traced silhouette (leaves the case at 11.25 mm, tips at 24.75 mm), inner edge along the window (one straight line fitted on all four arms), touching the end cap from 21.5 mm to the tip |
| Dial | Green-to-black gradient; applied light blue bar indices, minute ticks, eagle logo, EMPORIO ARMANI and the black date window at 3 stay in the dial map (flat); the EMPORIO ARMANI wordmark is redrawn sharp (Didot Bold fitted to each word's box, small eagle from the large one) because the photo smears it; hands, hub and their dark halos removed by a wide normalised blur fill |
| Hands | Light blue polished batons with round tips: hour 295.1°, minute 51.6°, seconds 207.5° (no counterweight visible), hub radius 0.98 mm |
| Crown | Black, fluted, at 90.6°, radius 2.9 mm, 21.34-24.18 mm |
| Bracelet | Rigid blue end cap between the arms, 22.31-28.64 mm, 19.63 mm wide; Milanese mesh 17.63 mm wide from under the case through the cap; house curl (7 mm) from the cap's outer end, since the cap is rigid and reaches past the lug tips. Mesh map: one 4.84 mm band below the 6 o'clock cap (two weave rows), tiled; the 12 o'clock side uses it turned round |

## Known gaps

- The photo is upscaled; dial print and the mesh weave are soft at close zoom.
- The 7 o'clock index under the seconds hand is partly filled with dial colour (the 3D seconds hand covers most of it).
- Indices are flat in the map, not raised.

## Phase 1 outputs

```sh
python3 -B -m pipeline.emporio_armani_ar11328_trace   # -> config/watches/emporio-armani-ar11328-trace.json
python3 -B -m pipeline.emporio_armani_ar11328_dial    # -> outputs/watches/emporio-armani-ar11328/dial_photo.jpg, mesh_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 54.9158 px/mm from the 43 mm case circle |
| Rings | crystal opening 17.39 mm, bezel top about 18.4-19.3 mm |
| Lugs | leave the case at 11.25 mm, tips 24.5 (12) / 25.0 (6), mean 24.75 mm; outer edge 18.5 mm |
| Caps | half width 9.815 mm, 22.31-28.64 mm |
| Mesh | half width 8.81 mm, weave repeat 133 px (4.84 mm, two rows) |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/emporio-armani-ar11328.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: blue anodised case and open lug arms, photo dial, light blue baton hands, black crown, blue end caps and Milanese mesh with the 7 mm curl |
| 1 | 2026-11-10 | EMPORIO ARMANI wordmark redrawn sharp in the dial map (Irsyad: text unclear) |
