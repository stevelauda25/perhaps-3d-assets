# Reference plan: ROLEX Explorer II 226570 (42 mm steel, white dial, fixed matt 24 h bezel, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from the Rolex image host (see `sources.md`; Catalog 2 tracker position 46). NEW MODEL (GMT-style 24 h hand, flat 24 h bezel, crown guards, date with Cyclops) adapted from the finished Rolex Air-King 126900 / Explorer 40 224270 builds (same Oyster family, same camera): the step is a variant-named copy (`pipeline/steps/watch_rolex_explorer2.py`, any number of hands, two aperture ellipses), the prep a variant-named copy (`pipeline/rolex_explorer2_prep.py`). Siblings build the Oyster Perpetual 41 lavender and the Submariner at the same time from their own files.

## Target asset

Front relief GLB `models/watches/rolex-226570.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, flat bezel with polished bevel, crystal, dial plate, four hands at different heights, hub, crown, bracelet rows, centre-link pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1028 x 1878 px incl. the crown | `rolex-226570_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Air-King template (back flat) |

## Phase 0 reading of the photo

White dial (the tracker says "white or black": the photo shows WHITE, matching the lead's file 0001), polished black-outlined white-lume circle indices at 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11 (as the circles at the 2, 4, 8, 10 positions and the baton indices at 3 / 6 / 9 as drawn), inverted triangle at 12, ROLEX with crown, OYSTER PERPETUAL DATE, orange EXPLORER II, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, date "28" under a Cyclops lens at 3 (flat window in the render: texture), engraved rehaut ring; fixed matt steel bezel with an engraved black 24 h scale (24, 2, 4, 8, 10, 12, 14, 16, 18, 20, 22 and triangle markers: texture), polished bevel inside; crown guards and a fluted crown at 3; Mercedes hour hand, sword minute hand, thin seconds hand with a tail disc and a lume ring, orange GMT hand with a hollow arrow head (pointing at about 5:30); Oyster bracelet.

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

See `config/watches/rolex-explorer2-226570-measure.json` (note field) and BASELINE.md.

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_explorer2.py` (variant copy of `watch_rolex_airking.py`: spec-driven hand list, window ellipse) |
| Prep | `pipeline/rolex_explorer2_prep.py` (variant copy of `rolex_explorer40_prep.py`: right-edge anchor, two ellipses, any hands) |
| Comparison frame | 1280 px square at half the native scale (11.3215 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_rolex_explorer2.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_explorer2_prep 226570   # -> config/watches/rolex-explorer2-226570-trace.json, outputs/watches/rolex-explorer2-226570/{dial_photo,steel_photo}.jpg
```
