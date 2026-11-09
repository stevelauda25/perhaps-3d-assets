# Reference plan: ROLEX Day-Date 40 228238 (40 mm yellow gold, fluted bezel, green ombre dial, President bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 row 67 (see `sources.md`). FOLLOWER of the finished Day-Date 40 228235 build (`../rolex-day-date-40-228235/baseline/BASELINE.md`): its step `pipeline/steps/watch_rolex_daydate40.py` and prep `pipeline/rolex_daydate40_prep.py` are used read-only (the prep reads everything from the `-measure.json` named by the key, so no variant-named copy was needed); only per-photo JSON and its own kit preset are new.

## Target asset

Front relief GLB `models/watches/rolex-228238.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, fluted bezel with 152 real facets, crystal, dial plate, Cyclops lens, three hands at different heights, hub, fluted crown, President bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright retailer render, transparent background, 2880 x 2880 RGBA PNG, the watch is 1541 x 2551 px incl. the crown, not centred | `rolex-228238-green_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Angled lifestyle photo of the same listing | none kept | not usable (set aside) |
| 3 | Side / back / crown close-up | none | not available; heights follow the 228235 template, back flat |

## Measured on this photo (continuous px of the native frame; full numbers in the `note` of `config/watches/rolex-daydate40-228238-measure.json`)

| Item | Result |
| --- | --- |
| Anchor | the listed 40 mm case = 2 x (case centre x 1437.7 - left flank x 716.64) = 1442.1 px, 36.053 px/mm (1.608 x the Rolex-host render's 22.42); the hands (8.60 / 13.86 / 14.04 mm) and the bezel flute radii (17.15 .. 19.60 mm) agree with the 228235 template to 0.1 mm, so the photo is a true 40 mm Day-Date at this scale |
| Pivot | hub cap (1438, 1260); the hand axes meet at (1433, 1263.5): a slightly raised camera shifts the planes (dial edge circle centre (1437.6, 1272.5), flange / rehaut circle (1441.4, 1257.2), flute face compromise (1439.5, 1265)) |
| Dial | green ombre (dark green rim to a lighter green centre), applied gold Roman numerals X (10), III (3), IV-like (6 / 8 / 4 clusters) and baton indices, day window THURSDAY at 12, date window 28 with a Cyclops at 3, rehaut engraved ROLEX; all native photo map |
| Hands | hour 305.21 deg (tip 8.60 mm, tail 2.68), minute 60.82 deg (13.86, 2.72, stepped sword tip with a slot), seconds 224.22 deg (14.04, 4.56, wide counterweight tail); traced from the thresholded photo inside edge-scan ROIs |
| Crown | fluted, axis 1.0 mm below the pivot, radius 2.95 mm, x 19.97 .. 22.73 mm |
| Bracelet | President: outer links (joints top 361 / 265 / 187, bottom 2310 / 2468 / 2604 / 2699) and polished centre links (top seams 408 / 315 / 219, bottom dark gaps 2236 / 2285 / 2387 / 2436 / 2554), ends 170 / 2715 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep | `pipeline/steps/watch_rolex_daydate40.py` and `pipeline/rolex_daydate40_prep.py`, read-only (key 228238 gives the file names `rolex-daydate40-228238-*`) |
| Comparison frame | 1600 px square at half the native scale (18.0265 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_rolex_daydate40_228238.json` (the watch reaches 40.5 mm below the pivot, so the 1280 frame of the template is too small) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daydate40_prep 228238   # -> config/watches/rolex-daydate40-228238-trace.json, outputs/watches/rolex-daydate40-228238/{dial_photo,steel_photo}.jpg
```
