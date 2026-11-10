# Reference plan: Emporio Armani Matteo AR11327 (matte gold aluminium, teal dial, gold mesh bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/emporio-armani-ar11327.glb`).
Template: the FS4735 round-case build (lathe, photo dial map, house curl), with this watch's own parts.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned ~13° toward the crown, white background, 3000 × 4962 | `front_3000x4962.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side, same case in blue | `three_quarter_blue_2718x3600.png` | HAVE, shapes and heights only (not measured) |
| 3 | Back | none | GAP: back is flat in the relief, not needed |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **43 mm** (listing), from the case height on the pivot column; end caps 20.15 mm wide |
| Photo turn | Dial ellipse ratio 0.9735 (~13°): horizontal sizes divided by it; the right lug arm shows its side, so the left arm is mirrored |
| Dial colour | Teal-green as in the photo; the listing says "purple" (likely an iridescent dial seen at another angle). Kept to the photo |
| Origin | Hand pivot (1378, 2440); dial ellipse centre (1388, 2444) |
| Dial | Eagle logo, EMPORIO ARMANI, minute marks, short 12 mark, date window and the purple-grey flange stay in the dial map; hands, hub and shadows removed by a normalised blur fill |
| Hour bars | Applied gold bars at every hour but 12, traced as rectangles (about 4.1 mm long) |
| Hands | Flat pale-gold sticks, no tails: hour 306.4°, minute 65.7°, seconds 357.7°; gold hub with a pin |
| Lugs | Open wire arms from the case flank to the end cap ends (left silhouette, 2.0 mm wide), open window between arm and case |
| End caps | Rectangular matte gold clamps, 22.65-28.22 mm from the pivot |
| Crown | Black knurled crown at 3, radius 2.86 mm, 22.27-25.87 mm |
| Bracelet | Gold mesh: photo tile (two weave rows, 139 px with a 26 px sideways step sheared out) repeating along the band, 18.4 mm wide; house 7 mm curl from the end caps' outer edge |
| Materials | Matte gold (roughness 0.45) for case, bezel, arms and end caps instead of the house steel; pale polished gold for hands, hub and bars |
| Branch, file | `main` (as the Fossil watches); `models/watches/emporio-armani-ar11327.glb` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.emporio_armani_ar11327_trace   # -> config/watches/emporio-armani-ar11327-trace.json
python3 -B -m pipeline.emporio_armani_ar11327_dial    # -> outputs/watches/emporio-armani-ar11327/dial_photo.jpg + mesh_tile.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 62.907 px/mm from the 43 mm case height |
| Rings | bezel groove 19.24 mm, dial 18.29 mm |
| Lug arms | leave the case at 14.75 mm, top end 24.4 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/emporio-armani-ar11327.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: matte gold case with domed bezel, wire lug arms, end caps, photo dial with applied bars, gold hands, black crown, mesh bracelet tile with the 7 mm curl |
