# Reference plan: ROLEX Submariner Date 126610LN (41 mm steel, black dial, black Cerachrom bezel, date with Cyclops lens, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Submariner 41 template built for the no-date 124060 (`../rolex-submariner-124060/baseline/BASELINE.md`), plus the Cyclops lens; this is the Submariner Date 41 template (126610LV, 126613LB, 126613LN follow).

## Target asset

Front relief GLB `models/watches/rolex-126610ln.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, Cyclops lens above the crystal, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1028 x 1855 px incl. the crown | `rolex-126610ln_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the 124060 template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | same camera as the 124060: alpha masks identical (0 px differ by > 60/255); scale 22.785 px/mm (41 mm = coin-edge tip diameter), pivot (960, 1424), ring centre (959.7, 1423.7); rings, crown box, lug rows and bracelet joints re-verified by overlay (see BASELINE) |
| Dial | black Maxi dial: Mercedes-ring hour hand, round indices 1 / 2 / 4 / 5 / 7 / 8, NO index at 3 (date window), bar at 9, long bar at 6, triangle at 12, ROLEX coronet, OYSTER PERPETUAL DATE, SUBMARINER 1000ft = 300m, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut ROLEX engraving |
| Date window / Cyclops | rounded lens with flat top (y 1355.5) and bottom (y 1487), bowed sides, x 1087.5..1254.5 (7.3 x 5.8 mm, centre 9.26 mm right of and 0.15 mm above the pivot), bright thin frame, a glass reflection arc; the white date window with the numeral inside (texture); the lens does NOT leave the crystal outline, the silhouette is unchanged |
| Hands (about 10:09:30) | hour 305.5 deg Mercedes, minute 63.55 deg, seconds 186.3 deg; traced outlines by the prep |
| Bezel / case / crown / bracelet | as the 124060 (same 41 mm Oyster case, black ceramic insert, 120-flute coin edge, fluted crown with guards, three-column Oyster bracelet) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_submarinerdate41.py` (copy of the Submariner 41 step plus the `date_cyclops` mesh from spec `date` and trace `date.lens_mm`); the 126610LV / 126613LB / 126613LN variants reuse it read-only |
| Prep | `pipeline/rolex_submarinerdate41_prep.py <key>` (copy of the Submariner 41 prep plus the lens outline from the measure key `date.lens_px`) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_submariner41.json` reused read-only (same pivot and scale) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_submarinerdate41_prep 126610ln   # -> config/watches/rolex-submarinerdate41-126610ln-trace.json, outputs/watches/rolex-submarinerdate41-126610ln/{dial_photo,steel_photo}.jpg
```
