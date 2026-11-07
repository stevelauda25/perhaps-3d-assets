# Reference plan: CARTIER Santos de Cartier Large WSSA0071 (39.8 mm steel, blue dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the Santos Large template built for the silver [WSSA0018](../cartier-santos-large-wssa0018/REFERENCE_PLAN.md): same step (`pipeline/steps/watch_cartier_santoslarge.py`) and prep (`pipeline/cartier_santoslarge_prep.py`), reused read-only; own measure / spec / job / kit preset.

## Target asset

Front relief GLB `models/watches/cartier-wssa0071.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, light background with soft shadow gradient, 750 x 750 JPEG without alpha | `cartier-wssa0071_original.jpg` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights are the template's estimates, back flat |

## Measured on this photo (px of the 750 x 750 frame)

| Item | Result |
| --- | --- |
| Crop | the same render as WSSA0018 at a 3.6 percent larger scale and another offset: the eight bezel screws match the silver ones by an isotropic scale of 1.036 and an offset of (-22.4, -22.0) (residual under 0.7 px); the bezel outline quarter mapped through it fits within 1 px at all four corners |
| Pivot | (364.6, 354.6) = intersection of the three hand centre lines (the hub ring's own circle fit gives (365.0, 355.7)); hub radius 9.3 px |
| Silhouette | derived mask (see `sources.md`), bbox x 207..559 (559 = crown halo), y 81..663 |
| Scale | case width 39.8 mm = about 317 px between the flanks (rows 262..288) gives 7.965 px/mm; horn-to-horn 397 px = 49.8 mm against the listed 47.5 mm (the same 4 percent as the silver photo; recorded, not asserted) |
| Case | polished bezel outline (template quarter mapped, mirrored about cx 366.1 / cy 358.7), eight screws radius 6.5 px, bezel opening x 253.0..476.5, y 242.5..462.0; dial rim x 259.5..475.0, y 250.5..458.5 (measured on this photo: the mapped silver values are up to 8 px off on the top and bottom edges); crown guards at x 541.5 |
| Dial | blue sunburst, Roman numerals (XII, I, X, XI, II ... with open IIII-type forms), square railroad minute track, CARTIER, AUTOMATIC, SWISS MADE, date window 18 at 6; all flat in the photo map |
| Hands (about 10:09) | steel sword hands: hour 7.96 mm at 305.5 deg, minute 11.51 mm at 49.9 deg, seconds 11.63 mm at 215.1 deg with a 4.95 mm tail at 35.3 deg (the thin blade runs into the VII numeral) |
| Crown | angular steel part x 518.5..543, half height 25.5 px, axis y 356.0, with the blue sapphire cabochon to x 556.2 |
| Bracelet | one column of links with two screws each; joints top 199.5 / 160.4 / 129.8 / 104.9 / 87.8 (end 81.5), bottom 511.0 / 550.0 / 589.0 / 623.2 / 649.5 (end 663.5); end link x 277.8..452.2 (top), 278.0..453.0 (bottom) |

## Decisions

| Decision | Answer |
| --- | --- |
| Silhouette | mask derived from the JPEG (no alpha), tolerance 5, recorded in `sources.md` and the trace |
| Hands | left in the dial map; 3D hands carry the front-projected photo with outlines measured from this photo (spec `hands.profile`) |
| Comparison frame | 1600 px square, camera 15.930 px/mm (own kit preset: the WSSA0018 preset's 15.276 does not fit this crop) centred on the pivot; the 2x photo is translated by (+69.8, +89.8) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.cartier_santoslarge_prep wssa0071   # -> 2x reference, mask, config/watches/cartier-santoslarge-wssa0071-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
