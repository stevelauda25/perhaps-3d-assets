# Reference plan: Zeppelin LZ126 Los Angeles GMT Z85963 (8596-3: steel, silver and blue world-map GMT dial, blue leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-10 (`models/watches/zeppelin-z85963.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3536 × 5456 (upscaled: about 25 px/mm of real detail) | `front_3536x5456.png` | HAVE, primary for everything |
| 2 | Back | none | Not needed for the flat-backed front asset |
| 3 | Side | none | GAP: heights fitted, not measured (listing: 14 mm thick) |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: strap 21.27 mm measured at 42 mm (strap width not listed) |
| Origin | Hand pivot (1623, 2663). The case circle centre sits 45 px lower (photo taken from below, case side visible at 6); the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z85963.glb` |
| Strap | Blue leather from the front photo with the house 7 mm curl from the lug tips; the photo cuts the top strap at 36.3 mm, the rolled-under end reuses the last row |
| Lugs | Polished like the case (photo), outline from the silhouette; the photo shows the bottom lugs longer (perspective), the model uses the mean tip (24.0 mm) |
| Print, numerals, GMT ring, embossed world map, airship logo, date window | Kept in the dial map (flat); hands, hub and their shadows removed from the map by a normalised blur fill |
| Hands | Black, non-metallic (photo); GMT triangle red |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, polished, wide sloped polished bezel (19.46-21 mm), high domed crystal |
| Lugs | Stepped polished horns outside the strap, tips at 24 mm (mean) |
| Dial | Silver outer zone with printed Breguet-style Arabic numerals and dot minute track, 24-hour GMT ring, blue waffle-textured centre with an embossed silver world map, Zeppelin airship logo, date window at 3 |
| Hands | Hour hand with an oval bulb, leaf minute hand, seconds needle with a lance counterweight, GMT needle with a red triangle, stacked black hub |
| Crown | Fluted onion crown with a domed end, at 3 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z85963_trace   # -> config/watches/zeppelin-z85963-trace.json
python3 -B -m pipeline.zeppelin_z85963_dial    # -> outputs/watches/zeppelin-z85963/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 70.3027 px/mm from the 42 mm case circle (fit on both flanks) |
| Rings | bezel inner 19.46 mm, dial visible to 18.80 mm |
| Lugs | leave the case at 14.75 mm, tips 22.75 (12) / 25.25 (6), mean 24.0 mm; outer edge 15.15 mm; strap half width 10.64 mm |
| Hands | hour 305.8°, 10.7 mm; minute 48.9°, 15.1 mm; seconds 210.6°, 15.6 mm; GMT 155.3°, 12.8 mm |
| Crown | 92.2°, radius 3.12 mm, reaches 25.1 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z85963.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: polished round case and lugs, photo dial, black hands with the red GMT triangle, fluted onion crown, blue leather strap with the 7 mm curl |
