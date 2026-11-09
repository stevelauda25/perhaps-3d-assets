# Reference plan: Zeppelin LZ129 Hindenburg Z70371 (7037-1: steel, silver moon-phase dial, black leather strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09 (`models/watches/zeppelin-z70371.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned toward the crown (3/4), 2000 × 3052 | `three_quarter_2000x3052.png` | HAVE, only photo; straightened (Irsyad chose this over waiting for a straight front) |
| 1b | Straight front of the same case (Z70363, blue dial) | `../zeppelin-z70363/front_2648.png` | Case, lug, crown and pusher sizes |
| 2 | Back | none | Not needed for the flat-backed front asset |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/zeppelin_z70371_rectify.py` maps the 12 black minute-track dots (60, 5 ... 55) of #1 to one circle with a homography
(median residual 0.5 px, max 0.8 px). The whole photo is warped, strap included.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **40 mm** (Irsyad, 2026-11-09), not the 36 mm on the spec sheet. Check: the strap at the 6 o'clock lug tips reads 20.1 mm at 40 mm, and the case/minute-track ratio matches Z70363 (40 mm) |
| Origin | Dial centre (minute-track centre). The raised hands are seen 0.57 mm off it (parallax of the 3/4 view); the model puts them on the centre |
| Case, lugs, crown, pusher | Same case as Z70363: round polished case with a thin sloped bezel, straight polished lugs outside a 20 mm strap, fluted crown at 3, plain pusher at about 4 |
| Hands | Black lacquered: hour hand with a bulb, lance minute hand, seconds needle with a gold counterweight, calendar-week needle with a red crescent tip, two sub-dial needles on gold hubs; outlines measured from the photo |
| Dial | Print, numerals, sub-dials and the moon window stay in the dial map; hands and hubs removed (normalised-blur fill) |
| Strap | Black leather, 20 mm; map straightened from the photo's 6 o'clock strap (the 12 o'clock one curls away) and used on both sides |

## Known gaps

- No straight front: the dial map is the straightened 3/4 photo. Print on the right side is slightly softer, and the crystal edge reflects the outer week numbers between the dial edge and the bezel on the right.
- The strap map ends 33.9 mm from the centre; past that the curled end repeats the last row.
- Lug tips and case flank heights are not visible in this photo; they follow Z70363.

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z70371_rectify   # -> outputs/watches/zeppelin-z70371/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.zeppelin_z70371_trace     # -> config/watches/zeppelin-z70371-trace.json
python3 -B -m pipeline.zeppelin_z70371_dial      # -> outputs/watches/zeppelin-z70371/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 43.3471 px/mm from the 40 mm case (left edge circle, concentric with the minute track) |
| Rings | minute-track dots 15.91 mm, dial edge 18.41 mm, bezel inner 18.50 mm |
| Hands | hour 307.7°, 10.15 mm; minute 55.2°, 15.35 mm; seconds 287.7°, 15.45 mm; week 131.8°, 14.92 mm |
| Sub-dials | centres ±7.61 mm on the 3-9 line |
| Strap | 20.1 mm at the 6 o'clock lug tips |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z70371.json --force
```

| Date | Change |
| --- | --- |
| 2026-11-09 | Round 1: first build; crystal base colour black so the black hands and print stay black. Delivered as `models/watches/zeppelin-z70371.glb` (1.10 MB) |
