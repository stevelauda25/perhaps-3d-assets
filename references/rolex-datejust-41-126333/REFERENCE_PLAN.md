# Reference plan: ROLEX Datejust 41 126333 (41 mm steel and yellow-gold Rolesor, yellow-gold fluted bezel, slate dial with green Roman numerals, Cyclops date, Jubilee bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). FOLLOWER of the Datejust 41 template built for the 126334 (`../rolex-datejust-41-126334/baseline/BASELINE.md`, section "Template for the next Datejust 41 variants"). Photo and SKU from Catalog 2 (see `sources.md`).

## Target asset

Front relief GLB `models/watches/rolex-126333.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, polished flange, chamfer and 74 real flutes of the yellow-gold bezel, crystal, dial plate, Cyclops lens, three gold hands at different heights, hub, fluted crown, Jubilee bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 969 x 1857 px incl. the crown | `rolex-126333_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the 126334 template, back flat |

## Measured on this photo (continuous px of the native frame; pivot (960, 1424), 22.2146 px/mm)

| Item | Result |
| --- | --- |
| Head (case, rings, flutes, crown, Cyclops window) | same camera and case as the 126334: values taken over from its measure file and verified by overlay (see BASELINE.md) |
| Dial | slate sunburst, green applied Roman numerals XII I II X III IIII VI V with polished frames, white lume bar at 9, gold coronet, ROLEX / OYSTER PERPETUAL / DATEJUST, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track engraved on the rehaut; texture only (dial map) |
| Hands (about 10:09:30) | gold baton hands with a dark facet and a white lume strip (hour 305.5 deg, minute 63.55 deg, seconds 186.3 deg gold needle with counterweight); traced by the variant prep with a chroma test (r - b >= 14 or white lume; the slate dial has r - b about 0, the green numerals are negative) |
| Bracelet | Jubilee: brushed steel outer links (joints top 904 / 807 / 730 / 685 / 674, bottom 1980 / 2107 / 2227 / 2331.5 / 2422 / 2490 / 2526) and three polished yellow-gold columns of 3 mm (column lines x 860 / 926.6 / 993.1 / 1059.6) with dark gap runs beside each polished block; joints in the spec `pieces_mm` |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_datejust41.py` READ-ONLY (columns outer / semi / centre / semi / outer from the spec) |
| Prep | variant copy `pipeline/rolex_datejust41_126333_prep.py` (only change: gold hand test via `hand_score` in the measure file; the template prep's colour test is for the green dial) |
| Kit / comparison frame | `config/presets/watch_kit_white_front_rolex_datejust41.json` READ-ONLY (11.1073 px/mm, 1280 px square on the pivot) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_datejust41_126333_prep 126333   # -> config/watches/rolex-datejust41-126333-trace.json, outputs/watches/rolex-datejust41-126333/{dial_photo,steel_photo}.jpg
```
