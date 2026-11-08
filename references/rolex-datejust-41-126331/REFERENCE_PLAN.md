# Reference plan: ROLEX Datejust 41 126331 (41 mm steel and Everose Rolesor, fluted Everose bezel, slate dial with green Roman numerals, Cyclops date, Jubilee bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Datejust 41 template built for the 126334 (`../rolex-datejust-41-126334/baseline/BASELINE.md`, "Template for the next Datejust 41 variants").

## Target asset

Front relief GLB `models/watches/rolex-126331.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, polished flange, chamfer and 74 real flutes of the Everose bezel, crystal, dial plate, Cyclops lens, three hands at different heights, hub, fluted crown, five-column Jubilee bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 969 x 1856 px incl. the crown | `rolex-126331_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the 126334 template, back flat |

## Checked against the 126334 photo (template registration)

Same alpha extent at the pivot row (x 505..1473), head silhouette rows 905..1980 differ by 277 px (one camera, one case, one bezel): pivot (960, 1424), scale 22.2146 px/mm, rings, 74 flutes, Cyclops window, crown and lug tips hold. Re-measured for this photo: hands (Everose, traced by a colour test), the Jubilee joints and column lines, the emissions.

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Dial | slate (dark grey) sunburst, applied Roman numerals with a green outline, a rose baton at 9, Everose crown at 12, ROLEX / OYSTER PERPETUAL / DATEJUST, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track with 5-minute numerals on the rehaut; all in the dial map |
| Hands (about 10:09:30) | hour 305.5 deg (tip 8.67 mm), minute 63.55 deg (13.41 mm), seconds 186.3 deg (14.29 mm, counterweight tail 4.68 mm); Everose polished faces with a dark brown facet and white lume strips; the traced outline = pixels with r - b >= 18 or grey >= 215 inside the ROI shapes, holes filled |
| Bracelet | Jubilee, five columns (steel outer / Everose semi / Everose centre / Everose semi / steel outer), column lines x 860.2 / 926.5 / 992.8 / 1059 (top), 859.5 / 926 / 993 / 1059.5 (bottom); the semi and centre joints are staggered; joints listed in the spec note; ends y 674.5 / 2525.5 (semis 2530) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / kit preset | `pipeline/steps/watch_rolex_datejust41.py` and `config/presets/watch_kit_white_front_rolex_datejust41.json` READ-ONLY (spec driven) |
| Prep | variant copy `pipeline/rolex_datejust41_126331_prep.py`: only the hand score differs (`hand_rose` in the measure file; the template's r / g colour test is for a green dial) |
| Comparison frame | 1280 px square at 11.1073 px/mm centred on the pivot (the template's) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_datejust41_126331_prep 126331   # -> config/watches/rolex-datejust41-126331-trace.json, outputs/watches/rolex-datejust41-126331/{dial_photo,steel_photo}.jpg
```
