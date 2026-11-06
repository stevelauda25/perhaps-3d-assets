# Reference plan: Seiko Pilot's Flight SNA411P1 on a black/red NATO strap (SNA411P1-VAR-NATO3)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo supplied by Irsyad on 2026-11-06.

## Target asset

A front-facing GLB in `models/watches/seiko-sna411p1-var-nato3.glb`, built like the other Seiko front reliefs: flat back, 2.5D depth, house curl.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front turned about 11° with perspective, white background, 2000 × 3070 | `turned_2000x3070.png` | HAVE, only photo |
| 2 | Straight front | none | MISSING (none exists): #1 is straightened instead |
| 3 | Side | none | heights fitted to the listed 13 mm |

## Straightening

`pipeline/seiko_sna411_rectify.py` maps the dial plane to a circle with a homography: eight lume dots to one radius at their hour angles, the 9 and 6 subdial hubs to a second radius (residual 1–5 px on the dots). Parts above the dial keep parallax (the photo was taken from the left): the insert's centre sits 0.81 mm left of the dial centre, the crystal ring 0.29 mm, the hand pivot 0.41 mm. The build maps the insert around its own photo centre. The 12 o'clock lug and strap end rise toward the camera; the 6 o'clock values are mirrored.

## Scale anchors

| Dimension | Value |
| --- | --- |
| Coin-edge bezel | **42 mm** (anchor, Irsyad, 2026-11-06; listing says 46 mm case) |
| Insert, crystal | 40.66, 33.49 mm |
| Lug to lug | 46.34 mm (6 o'clock lug mirrored) |
| Strap | 22 mm NATO (photo 22.9 mm with its side wall) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, polished, under the bezel | #1 |
| Bezel | Coin edge (about 56 scallops), black slide-rule insert with white and yellow print | #1, insert from the photo map |
| Dial | Black with the inner slide rule, tachymeter, three subdials (MIN at 12, SEC at 9, ALARM at 6) with their hands, SEIKO, date at 3 | photo map |
| Lume dots | Applied dots at 1 2 4 5 7 8 10 11 | raised discs textured by the map |
| Hands | Sword hour and minute with lume; yellow chrono seconds needle with a triangular counterweight | #1 |
| Crown, pushers | Short wide fluted crown with a rounded end at 3; pushers at 2 and 4 with a fluted screw-down collar and a plain domed button | #1 |
| Strap | Black/red striped NATO (black, red, black, red, black) | straightened atlas from the 12 o'clock end |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 42 mm bezel (Irsyad, 2026-11-06) |
| Subdial hands | Stay in the photo map (flat) |
| NATO keepers | Not modelled; the strap ends with the house curl |
| Hand pose | The photo's pose (10:08, chrono at zero) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_sna411_rectify   # -> outputs/watches/seiko-sna411p1-var-nato3/front_rectified.png
python3 -B -m pipeline.seiko_sna411_trace     # -> config/watches/seiko-sna411p1-var-nato3-trace.json
python3 -B -m pipeline.seiko_sna411_map       # -> outputs/watches/seiko-sna411p1-var-nato3/dial_photo.jpg, strap_photo.jpg
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-sna411p1-var-nato3.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief from the straightened photo |
| 2 | 2026-11-06 | Crown and pushers reshaped from the photo (Irsyad): short wide crown (6.0 mm across, 3.8 mm out, deep flutes, rounded end); pushers as a fluted collar plus a plain domed button |

## Known gaps and artefacts

- Only one turned photo: the dial map is resampled (straightened), slightly softer than a straight photo.
- Print under the hour, minute and chrono hands is filled from rotated dial content; the hand geometry covers it at the photo pose.
- Lug shape and case heights are estimates.
