# Reference plan: Seiko 5 SNXS75K1 (grey dial, gold accents, day-date, steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 4 committed 2026-11-09 (models/watches/seiko-snxs75k1.glb).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, turned about 11° toward the crown, white, 2800 × 2800 | `front_ashford_2800x2800.jpg` | HAVE, primary. No straight front photo exists online; straighten the dial plane with a homography (as `pipeline/seiko_sna411_rectify.py`) |
| 2 | 3/4 from the crown side, white, 2000 × 3358 | `turned_crown_2000x3358.png` | HAVE: crown position, case flank, lug slope |
| 3 | Back, white, 1200 × 1200 | `back_1200x1200.jpg` | HAVE, not needed for a front relief |
| 4 | Side profile | none | GAP: heights from the listed 11.5 mm thickness (SNK381K1/SNK607K1 heights scaled) |

## Measured on the front photo (Phase 0, ±5 px)

| Item | Pixels | Note |
| --- | --- | --- |
| Hand pivot | (1345, 1313) | Origin |
| Minute track, outer tick ends | 1024 wide × 1045 high, centre (1370, 1327) | Ratio 0.98: turned about 11° about the vertical axis |
| Case face, row y 1313 | x 703 to 2030 = 1327 | Right flank visible 2030 to 2097 |
| Lug gap (end link), top and bottom | 714 / 715 | |
| Lug tips | y 517 to 2142 = 1625 | |

At 36.8 mm: about 36.8 px/mm, lug gap reads about 19.8 mm (19 mm listed), lug to lug about 44.2 mm. At 37 mm: lug gap 19.7 mm.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **36.8 mm** (Irsyad, 2026-11-09). The listed 19 mm lug width reads 19.8 mm at this scale; 19 mm would mean a 35.3 mm case, which no listing gives |
| Front photo | Ashford photo straightened (Irsyad, 2026-11-09) |
| Bracelet | Three brushed columns from the photo, house 7 mm curl from the lug tips; clasp left out |
| Case finish | Polished case and bezel, brushed lugs top, end links and bracelet |

## Parts seen

| Part | True shape |
| --- | --- |
| Case | Round, polished, wide sloping bezel; black gasket ring between bezel and dial; lugs are flat brushed blocks continuous with the case shoulders |
| Dial | Grey sunburst; printed black minute ticks, AUTOMATIC, 7S26 line; applied gold SEIKO and 5 shield |
| Indices | Applied, gold frame with lume inlay: double bar at 12, wide bar at 9 and 6, single bars elsewhere; day-date window at 3 |
| Day-date | Gold frame, white discs, day and date |
| Hands | Hour and minute: gold frame with lume inlay; gold seconds needle with a short counterweight |
| Crown | Small, fluted, recessed in the flank at about 4 o'clock (measure in Phase 1) |
| Bracelet | Three columns, wider centre link, brushed; end links fill the lug gap |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snxs75_rectify   # -> outputs/watches/seiko-snxs75k1/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.seiko_snxs75_trace     # -> config/watches/seiko-snxs75k1-trace.json
python3 -B -m pipeline.seiko_snxs75_dial      # -> outputs/watches/seiko-snxs75k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Straightening | Homography from 45 printed minute ticks to one circle (the shaded upper left has none); residual median 1.2 px, max 4.0 px |
| Scale | 37.31 px/mm from the case face (left edge to the face/flank edge on the right) = 36.8 mm; origin = dial centre (1400, 1400) |
| Rings | dial edge 15.06 mm, gasket outer (crystal) 15.81 mm, bezel slope to 16.89 mm, bezel top to 18.31 mm |
| Lug tips | 21.4 mm (12), 21.6 mm (6), mean 21.5 mm; lug to lug 43.0 mm |
| End link and first bracelet row | 19.8 mm (19 mm listed) |
| Indices | 9.43–13.12 mm; 1.37 mm wide, 2.18 mm at 6 and 9, 2.68 mm for the pair at 12 |
| Hands (10:09:42) | hour 306.8°, 8.73 mm, 1.34 mm wide; minute 54.5°, 12.58 mm, 0.96 mm wide; seconds 252.5°, 12.67 mm, tail 4.13 mm |
| Bracelet | pitch 4.6 mm (first outer row; later rows curve away), centre links 0.48 of the half width, half a row off the outer links |

The hand pivot stands 0.46 mm left of and 0.19 mm above the dial centre in the straightened photo (parallax of the raised
hub); the build puts the hands on the dial centre. The dial map fills hand zones by 6° rotations; its lighting is bridged
along the angle in polar coordinates (the sunburst's brightness follows the angle), the hub zone takes the dial from further
out along the same angle.

Artefacts not traced: the right flank and the bracelet side show (photo turned); the left of the dial sits in the shadow of
the inner wall and stays darker in the dial map; the marker at 3 is a sliver under the gasket and stays in the dial map.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snxs75k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: polished steel case, gold-framed indices and baton hands with lume, gold day-date frame, three-column brushed bracelet 19.8 mm with the 7 mm curl; 1.1 MB GLB |
| 2 | 2026-11-09 | Colours set in model-viewer 4.1.0 to Irsyad's photo: dial grey (about 119 vs 108 there), dark brass hands, index frames and logo (hands about 132/124/92 vs 130/121/90), black print restored, sunburst contrast 1.4; blunt hand ends, hands 1.34 / 0.96 mm wide |
| 3 | 2026-11-09 | Dark brass gold (model-viewer about 132/124/92); SEIKO and 5 shield set apart in the dial map (about 119/104/69 and 149/133/102 vs 124/111/80 and 151/135/100 in the photo), logo contrast 1.6; dial specular 0.1 so model-viewer does not wash the dial out |
| 4 | 2026-11-09 | SEIKO and the 5 shield taken from Irsyad's photo (`turned_crown_2000x3358.png`) by a 9-point homography, seconds hand removed (rim mirrored, face inpainted), shifted to the map's dial grey (Irsyad: must match exactly) |
