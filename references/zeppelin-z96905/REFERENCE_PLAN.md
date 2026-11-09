# Reference plan: Zeppelin Mediterranée Z96905 (9690-5: steel, beige power-reserve dial, brown leather strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-09 (`models/watches/zeppelin-z96905.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2730 × 3940 | `front_2730x3940.png` | HAVE, primary for everything |
| 2 | 3/4, side, back | none | GAP: heights fitted, not measured |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: strap 21.1 mm measured at 42 mm (strap width not listed) |
| Origin | Hand pivot (1249, 1911); the case circle centre is within 1 px |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z96905.glb` |
| Strap | Brown leather from the front photo with the house 7 mm curl from the lug tips; past the photo's strap end the rolled-under end reuses the last row |
| Lugs | Polished, stepped: outer block plus a step 1 mm lower next to the strap, split at 12.19 mm |
| Print, applied numerals, Z logo, sub-dial rings, date window, pulsometer flange | Kept in the dial map; the flange is a cone from 16.34 to 19.05 mm. Hands, hubs and their shadows removed from the map by a normalised blur fill |
| Hands | Black (lacquered), non-metallic; gold pins in the hubs |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, polished, wide polished bezel (19.26-21 mm), domed crystal |
| Lugs | Stepped polished lugs outside the strap, outer edge 14.9 mm, tips at 23.9 mm |
| Dial | Beige, applied gold Arabic numerals, minute track, sloped pulsometer flange (base 30), power reserve at 12, day sub-dial at 9, 24 h sub-dial with date window at 6, Z logo and Méditerranée script at 3 |
| Hands | Needle hour hand with a teardrop bulb, lance minute hand, seconds needle with a diamond counterweight, stacked black centre hub with a gold pin; day and 24 h hands with paddle tails, power-reserve hand with a lance section |
| Crown | Fluted, domed end, at 3 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z96905_trace   # -> config/watches/zeppelin-z96905-trace.json
python3 -B -m pipeline.zeppelin_z96905_dial    # -> outputs/watches/zeppelin-z96905/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 53.9055 px/mm from the 42 mm case circle (fit on both flanks) |
| Rings | bezel inner 19.26 mm, flange inner (flat dial edge) 16.34 mm |
| Lugs | leave the case at 15.0 mm, tips 24.0 (12) / 23.75 (6), mean 23.875 mm; outer edge 14.9 mm; step at 12.19 mm; strap half width 10.55 mm |
| Hands | hour 302.1°, 10.3 mm; minute 36.8°, 15.0 mm; seconds 41.1°, 15.7 mm |
| Crown | 90°, radius 3.06 mm, flutes 20.4-23.7 mm, dome to 25.1 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z96905.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: polished round case and stepped lugs, photo dial with the pulsometer flange as a cone, black hands and hubs with gold pins, fluted domed crown, brown leather strap with the 7 mm curl |
