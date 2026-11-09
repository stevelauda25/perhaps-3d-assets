# Reference plan: Zeppelin Mediterranee 1921 Z96643 (steel, blue sunburst day-date dial, brown leather strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09 (`models/watches/zeppelin-z96643.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, slightly from below and right, 2160 × 3092 | `front_2160x3092.png` | HAVE, only photo; straightened |
| 2 | Back | none | Not needed for the flat-backed front asset |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/zeppelin_z96643_rectify.py` maps the 12 white hour bars on the minute track to one circle with a homography
(median residual 0.57 px, max 1.22 px).

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **40 mm** (listing). Check: the strap between the lugs reads 19.2-19.3 mm at 40 mm (a 20 mm strap would make the case 41.5 mm) |
| Origin | Dial centre (hour-bar centre). The raised hub is seen 0.5 mm up-left of it and the case top 0.56 mm left (parallax); the model puts both on the centre |
| Case | Round polished case with a wide domed polished bezel (18.25-20 mm); sloped minute ring 15.68-18.25 mm |
| Lugs | Stepped: an outer polished part (silhouette traced about the case centre) and a lower inner rail beside the strap, groove at 11.15 mm |
| Hands | White hour hand with a bulb, white lance minute hand, white seconds needle with a pale gold counterweight, stacked gold hub; outlines measured from the photo |
| Dial | Applied cream numerals, logo, print, minute ring and the day-date window stay in the dial map; hands and hub removed (pattern copied a few degrees round the sunburst) |
| Crown | Fluted (16), domed end, at 3, radius 2.53 mm, to 23.07 mm |
| Strap | Brown leather, 19.3 mm; map straightened from the photo's 12 o'clock strap (the 6 o'clock one carries an embossed logo), used on both sides |

## Known gaps

- The strap map covers 21.2-29.8 mm from the centre; past that the curled end repeats the last row. The embossed Zeppelin logo on the 6 o'clock strap is not reproduced.
- Lug and bezel heights are not visible in a front photo; they follow the Hindenburg builds.

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z96643_rectify   # -> outputs/watches/zeppelin-z96643/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.zeppelin_z96643_trace     # -> config/watches/zeppelin-z96643-trace.json
python3 -B -m pipeline.zeppelin_z96643_dial      # -> outputs/watches/zeppelin-z96643/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 43.5651 px/mm from the 40 mm case (left and right edge circles) |
| Rings | hour bars 14.35 mm, minute ring 15.68-18.25 mm |
| Lugs | outer edge 13.58 mm, groove 11.15 mm, strap edge 9.66 mm, tips 22.5 mm |
| Hands | hour 304.9°, 10.23 mm; minute 49.4°, 13.88 mm; seconds 119.6°, 15.16 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z96643.json --force
```

| Date | Change |
| --- | --- |
| 2026-11-09 | Round 1: first build. Delivered as `models/watches/zeppelin-z96643.glb` (1.15 MB) |
