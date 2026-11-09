# Reference plan: Zeppelin LZ129 Hindenburg Z70363 (7036-3: steel, blue moon-phase dial, blue leather strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 2 committed 2026-11-09 (`models/watches/zeppelin-z70363.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2648 × 2648 | `front_2648.png` | HAVE, primary for everything |
| 1b | Front turned toward the crown, 2000 × 3140 | `three_quarter_2000x3140.png` | Crown, pusher, crystal dome; strap colour differs (dark), not used for colour |
| 2 | Back | none | Not needed for the flat-backed front asset |
| 3 | Side | none | GAP: heights fitted, not measured |
| 4 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **40 mm** (listing, confirmed by Irsyad 2026-11-09). Check: strap 19.65 mm measured at 40 mm vs 20 mm; the listing's 10 mm lug width is wrong |
| Origin | Hand pivot (1319, 1282). The case circle centre sits 6 px lower (photo taken slightly from below); the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z70363.glb` (Irsyad 2026-11-09) |
| Strap | Blue leather from the front photo with the house 7 mm curl from the lug tips; the photo cuts the top strap at 33.4 mm, the rolled-under end reuses the last row |
| Lugs | Polished like the case (photo), not the house brushed lugs |
| Print, numerals, sub-dial rings, moon window, airship logo | Kept in the dial map (flat); hands, hubs and their shadows removed from the map by a normalised blur fill |
| Moon window | From the turned photo (moon on the left, stars on the right; Irsyad 2026-11-09: the front photo's window reads as flipped), registered by a dial homography and colour-matched; the same photo fills the dial under the front photo's seconds needle |
| Hands | White, non-metallic (as they read in the photo); thin polished-steel needles reflected the dark surroundings and disappeared |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, polished, thin sloped polished bezel (18.9-20 mm), domed crystal |
| Lugs | Straight polished horns outside the strap, 2.8 mm wide, tips at 22 mm |
| Dial | Navy sunray, outer week scale 1-52 and minute track, Breguet-style printed Arabic numerals, applied airship logo, day sub-dial at 9, date sub-dial at 3, moon window at 6 |
| Hands | Lance hour hand with an airship bulb, lance minute hand, seconds needle with a rose gold counterweight, calendar-week hand with a rose gold crescent, sub-dial needles on rose gold hubs, stacked rose gold centre hub |
| Crown | Fluted, conical collar, at 3 |
| Pusher | Plain cylinder with a stem, at about 4 (119.5 deg) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z70363_trace   # -> config/watches/zeppelin-z70363-trace.json
python3 -B -m pipeline.zeppelin_z70363_dial    # -> outputs/watches/zeppelin-z70363/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 35.0928 px/mm from the 40 mm case circle (fit on both flanks) |
| Rings | bezel inner 18.92 mm, dial visible to 18.12 mm |
| Lugs | leave the case at 15.75 mm, tips 21.75 (12) / 22.25 (6), mean 22.0 mm; outer edge 12.61 mm; strap half width 9.82 mm |
| Hands | hour 302.8°, 12.1 mm; minute 55.2°, 16.4 mm; seconds 227.2°, 16.2 mm; week 138.8° |
| Crown | 90.7°, radius 3.08 mm, reaches 23.1 mm; pusher 119.5°, head radius 1.71 mm, reaches 23.05 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z70363.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: polished round case and lugs, photo dial, lance hands with rose gold parts, fluted crown and pusher, blue leather strap with the 7 mm curl |
| 2 | 2026-11-09 | Moon window from the turned photo (moon left, stars right); dial under the seconds needle from the same photo; white hands |
