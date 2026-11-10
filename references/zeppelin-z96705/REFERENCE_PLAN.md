# Reference plan: Zeppelin Mediterranee 1921 chronograph Z96705 (9670-5: steel, cream dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/zeppelin-z96705.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3200 × 4832 | `front_3200x4832.png` | HAVE, primary for everything |
| 2 | Back | none | Not needed for the flat-backed front asset |
| 3 | Side | none | GAP: heights fitted, not measured (listing: 12 mm thick); pusher height assumed |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: strap 20.75 mm measured at 42 mm vs 22 mm listed; the other 42 mm Zeppelins measure 21.1-21.5 mm the same way |
| Origin | Hand pivot (1528, 2347); the case circle centre sits 19 px lower, the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z96705.glb` |
| Strap | Brown leather from the front photo with the house 7 mm curl from the lug tips |
| Lugs | Polished like the case (photo), outline from the silhouette, top and bottom lugs stretched to the mean tip |
| Print, numerals, tachymeter, sub-dial scales, airship logo, date window | Kept in the dial map (flat); hands, hubs and their shadows removed from the map by a normalised blur fill |
| Hands | Black, non-metallic (photo) |
| Pushers | Rectangular polished blocks at 2 and 4 (photo); their faces read dark in the photo from reflection |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, polished, sloped polished bezel (19.66-21 mm), domed crystal |
| Lugs | Stepped polished horns outside the strap, tips at 24.5 mm (mean) |
| Dial | Cream, printed gold Arabic numerals, tachymeter and minute scales, small seconds at 9, 30-minute counter at 3 with the date window, airship logo |
| Hands | Hour hand with an oval bulb, leaf minute hand, centre chronograph needle with a lozenge counterweight, two sub-dial needles with lozenge tails, stacked black hub |
| Crown | Fluted onion crown with a domed end, at 3 |
| Pushers | Rectangular, at 59.5° and 119.5° |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z96705_trace   # -> config/watches/zeppelin-z96705-trace.json
python3 -B -m pipeline.zeppelin_z96705_dial    # -> outputs/watches/zeppelin-z96705/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 59.5038 px/mm from the 42 mm case circle (fit on both flanks) |
| Rings | bezel inner 19.66 mm, dial visible to 18.02 mm |
| Lugs | leave the case at 14.75 mm, tips 24.25 (12) / 24.75 (6), mean 24.5 mm; outer edge 15.23 mm; strap half width 10.38 mm |
| Crown | 90.5°, radius 2.82 mm, reaches 25.6 mm |
| Pushers | half width 2.86 mm, reach 22.7 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z96705.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: polished round case and lugs, photo dial, black hands and sub-dial needles, fluted onion crown, rectangular pushers, brown leather strap with the 7 mm curl |
