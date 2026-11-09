# Reference plan: Zeppelin Mediterranee 1921 Z96645 (steel, cream day-date dial, black hands, brown leather strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09 (`models/watches/zeppelin-z96645.glb`).

Same model and case as [Z96643](../zeppelin-z96643/REFERENCE_PLAN.md); scripts, step and spec are copies of its files under this SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, slightly from below and right, 3218 × 4988 | `front_3218x4988.png` | HAVE, only photo; straightened |
| 2 | Back | none | Not needed for the flat-backed front asset |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/zeppelin_z96645_rectify.py` maps the 12 black hour bars on the minute track to one circle with a homography
(median residual 0.45 px, max 0.55 px).

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **40 mm** (spec sheet). Check: the strap between the lugs reads 19.2-19.7 mm |
| Origin | Dial centre (hour-bar centre); the raised hub is seen 0.19 mm off it, the model puts it on the centre |
| Case, lugs, crown | Same case as Z96643: wide domed polished bezel, stepped lugs (outer part and inner rail), fluted crown with a domed end (crown sizes from Z96643) |
| Hands | Black hour hand with a bulb, black lance minute hand, black seconds needle with a black counterweight, black hub; outlines measured from the photo |
| Dial | Cream; applied gold numerals, logo, print, minute ring and the day-date window stay in the dial map; hands, their shadows and the hub removed (smooth blur fill) |
| Strap | Brown leather, 19.7 mm; map straightened from the photo's 12 o'clock strap, used on both sides |

## Known gaps

- The hand zones in the dial map are smooth (no dial grain); the 3D hands cover them from the front.
- Crystal glare at 9-10 o'clock on the minute ring stays in the dial map.
- The strap map covers 21.2-31.3 mm from the centre; past that the curled end repeats the last row. The embossed Zeppelin logo on the 6 o'clock strap is not reproduced.

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z96645_rectify   # -> outputs/watches/zeppelin-z96645/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.zeppelin_z96645_trace     # -> config/watches/zeppelin-z96645-trace.json
python3 -B -m pipeline.zeppelin_z96645_dial      # -> outputs/watches/zeppelin-z96645/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 67.8656 px/mm from the 40 mm case (left and right edge circles) |
| Rings | hour bars 14.17 mm, minute ring 15.49-18.02 mm |
| Lugs | outer edge 13.83 mm, groove 11.26 mm, strap edge 9.86 mm, tips 22.25 mm |
| Hands | hour 302.9°, 10.47 mm; minute 45.5°, 14.64 mm; seconds 291.5°, 14.77 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z96645.json --force
```

| Date | Change |
| --- | --- |
| 2026-11-09 | Round 1: first build. Delivered as `models/watches/zeppelin-z96645.glb` (1.91 MB) |
