# Reference plan: Armani Exchange AX1903 (16-sided polished steel case, white dial with black batons, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 for review.
Template: the FS4735 leather-strap build (photo map for dial and strap, house curl), with this watch's own case, hands and crown.
File name `armani-ax1903`: the tracker matches the first word of the title (`Armani`) plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, transparent background, 4020 × 5202 | `front_4020x5202.png` | HAVE, primary for everything (an upscale: soft print) |
| 2 | Slight 3/4 from the crown side | `three_quarter_3000x4212.png` | HAVE, heights and part shapes only (not measured) |
| 3 | Back | none | GAP: back is flat in the relief, not needed |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **44 mm** across the 9-3 flats (listing). Check: strap 21.91 mm measured (22 mm usual for this case) |
| Origin | Hand pivot (1894, 2600), on the case's mirror line |
| Case | 16 flats: 8 long ones at 0, 45, 90 ... deg (22.0 mm from the centre) and 8 short ones between them (22.63 mm). Lofted from polygon rings (flank, sloped outer bezel band, near-flat top to the inner polygon edge 3.46 mm in) into round rings (inner bevel 17.84 mm, crystal 17.15 mm). 11 mm thick listing |
| Crown guard | One shoulder around the crown, outline from the right silhouette (to 24.7 mm), top falling toward the crown |
| Bezel marker | Two red stripes at 12 on the sloped bezel top, trapezoids from the photo |
| Lugs | Wide polished lugs from the left silhouette (leave the 45 deg flat at 15.5 mm), slanted tip, sloped top |
| Dial | Indices, minute track dots, ARMANI EXCHANGE and the line-textured centre disc stay in the dial map (flat, printed in the 3/4 view); hands, the AX fork and their shadows removed by a coarse plus fine normalised blur fill |
| Hands | White sword hour and minute hands (1.05 mm wide, grey edges) with black tips (hour: round-ended needle, minute: lance); black AX fork around the pivot traced from the photo; black seconds needle with a white stripe and red tip |
| Crown | Radius 3.27 mm, smooth collar (2.54 mm) 22.1-23.5 mm, fluted body to 25.4 mm with a chamfered end |
| Strap | Brown leather from the front photo with the house 7 mm curl from the lug tips; the photo's strap ends at 39.4 mm, the rolled end reuses that row |

## Phase 1 outputs

```sh
python3 -B -m pipeline.armani_ax1903_trace   # -> config/watches/armani-ax1903-trace.json
python3 -B -m pipeline.armani_ax1903_dial    # -> outputs/watches/armani-ax1903/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 64.9545 px/mm from the 44 mm case flats |
| Rings | crystal 17.15 mm, inner bevel top 17.84 mm, dial flat (track dots) 16.63 mm |
| Lugs | leave the case at 15.5 mm, tips 25.5 mm; outer edge 16.0 mm; strap half width 10.95 mm |
| Hands | hour 299.9°, minute 59.8°, seconds 210.1° |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/armani-ax1903.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: 16-sided polished case with crown guard and red stripes, photo dial, white sword hands with the black AX fork, black seconds needle, fluted crown, brown leather strap with the 7 mm curl |
