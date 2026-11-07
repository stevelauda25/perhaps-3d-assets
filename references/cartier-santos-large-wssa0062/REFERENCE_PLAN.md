# Reference plan: CARTIER Santos de Cartier Large WSSA0062 (39.8 mm steel, green dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the Santos Large template built for the silver [WSSA0018](../cartier-santos-large-wssa0018/REFERENCE_PLAN.md) and of the blue follower [WSSA0071](../cartier-santos-large-wssa0071/REFERENCE_PLAN.md): same step (`pipeline/steps/watch_cartier_santoslarge.py`) and prep (`pipeline/cartier_santoslarge_prep.py`), reused read-only; own measure / spec / job / kit preset.

## Target asset

Front relief GLB `models/watches/cartier-wssa0062.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, light background with soft shadow gradient, 750 x 750 JPEG without alpha | `cartier-wssa0062_original.jpg` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights are the template's estimates, back flat |

## Measured on this photo (px of the 750 x 750 frame)

| Item | Result |
| --- | --- |
| Crop | the same render as WSSA0018 / WSSA0071 at another scale and offset: the eight bezel screws match the 0071 ones by an isotropic scale of 1.0229 and an offset of (6.16, -8.02) (residual under 0.5 px); the template outlines mapped through it fit within about 1 px (gridded 4x overlays) |
| Pivot | (379.3, 354.8) = intersection of the three hand centre lines (residuals 0.1 to 0.4 px) |
| Silhouette | derived mask (see `sources.md`), rows 75..669, crown dome to x 575 |
| Scale | case width 39.8 mm = about 324 px between the flanks (rows 262..288) gives 8.141 px/mm; horn-to-horn 49.9 mm against the listed 47.5 mm (the same 4 percent as the other photos; recorded, not asserted) |
| Case | polished bezel outline, eight screws, opening and dial rim mapped from the template and verified on overlays |
| Dial | green sunburst, Roman numerals, square railroad minute track, CARTIER, AUTOMATIC, SWISS MADE, date window 18 at 6; all flat in the photo map |
| Hands (about 10:09) | steel sword hands: hour 8.03 mm at 305.4 deg, minute 11.47 mm at 50.3 deg, seconds 11.61 mm at 218.0 deg with a 4.81 mm tail at 38.6 deg |
| Crown | angular steel part with the blue sapphire cabochon, x 536.5..575, axis y 356.2 |
| Bracelet | one column of links with two screws each; joints top 196.0 / 156.0 / 125.0 / 98.3 / 82.0 (end 75.4), bottom 515.0 / 554.3 / 594.0 / 629.2 / 654.6 (end 669.5); end link x 290.0..469.0 (top), 290.8..469.8 (bottom) |

## Decisions

| Decision | Answer |
| --- | --- |
| Silhouette | mask derived from the JPEG (no alpha), tolerance 5, recorded in `sources.md` and the trace |
| Hands | left in the dial map; 3D hands carry the front-projected photo with the WSSA0071 steel-hand outlines stretched to the lengths measured here |
| Comparison frame | 1600 px square, camera 16.281 px/mm (own kit preset) centred on the pivot; the 2x photo is translated by (+40.4, +89.4) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.cartier_santoslarge_prep wssa0062   # -> 2x reference, mask, config/watches/cartier-santoslarge-wssa0062-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
