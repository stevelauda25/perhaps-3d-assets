# Reference plan: ROLEX Submariner Date 116610LV "Hulk" (40 mm steel, green sunburst Maxi dial, green Cerachrom bezel, Cyclops date, Oyster bracelet)

Phase 0 (draft, finished in BASELINE.md). Photo from the retailer wristcheck.com (see `sources.md`). FOLLOWER of the Submariner Date 41 builds (`../rolex-submariner-date-126610lv/baseline/BASELINE.md`).

## Target asset
Front relief GLB `models/watches/rolex-116610lv.glb`, flat back, layered meshes (case with lugs and crown guards, green ceramic bezel insert, rim, coin-edge ring, crystal, dial, Cyclops lens, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held
| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, retailer render, transparent background, 2880 x 2880 RGBA PNG, watch bbox x 722..2292, y 193..2705 (not centred) | `rolex-116610lv_original.png` | HAVE (untouched, native size; somewhat soft / upscaled) |
| 2 | Side / back | none | not available; heights follow the template, back flat |

## Measured (see the measure JSON and BASELINE.md)
Scale 35.6 px/mm (coin-edge tip diameter 40 mm = 2 x 712 px), pivot (1435, 1434), ring centre (1434.2, 1430.3), rings dial 474 / crystal 542.5 / insert 547.5..672.5 / rim 678 / tips 712 px. Different from the 41 mm Rolex-host builds: older 40 mm case, narrower lugs and the old end links, Maxi dial with the thicker hub, green sunburst dial, bezel rotated about 2.6 deg (the 12 pip is right of the dial axis; projected photo, no geometry impact), smooth circular coin-edge silhouette (scallops are inside the face), hands at 10:09.

## Decisions
Step `pipeline/steps/watch_rolex_submarinerdate41.py` reused READ-ONLY; prep copy `pipeline/rolex_submarinerdate40_prep.py` (only the file prefix changed: the 41 prep hardcodes `rolex-submarinerdate41-`); own kit preset `config/presets/watch_kit_white_front_rolex_submarinerdate40.json`. Tracker variant "green" matches the photo (green dial and bezel).

## Phase 1 outputs
```sh
python3 -B -m pipeline.rolex_submarinerdate40_prep 116610lv
```
