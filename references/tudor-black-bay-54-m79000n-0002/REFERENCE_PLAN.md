# Reference plan: TUDOR Black Bay 54 M79000N-0002 (37 mm steel, black dial, black rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Variant of the [Black Bay 54 -0001 build](../tudor-black-bay-54-m79000n-0001/REFERENCE_PLAN.md) (template: case, bezel, crown, hands, dial map); only the strap is new.

## Target asset

Front relief GLB `models/watches/tudor-m79000n-0002.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79000n-0002_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the -0001 build, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Registration to -0001 | the case, bezel, crown, dial and hands coincide with the -0001 photo (shift search +-2 px: best at 0, 0), so pivot (451, 653), scale 13.946 px/mm (37 mm anchor), rings, crown box and hand axes are the -0001 values (`config/watches/tudor-bb54-m79000n-0002-measure.json`) |
| Alpha bbox | x 193..740, y 213..1123 (centre section ends 213 and 1123, side sections 214..216 and 1120..1122); rubber runs 440 px (31.55 mm) above and 470 px (33.7 mm) below the pivot at the centre section |
| Strap | black rubber in three vertical sections: seams at x ~388.5 / ~510.5 (top), ~389.5 / ~508.5 (bottom end, converging slightly); side sections end on the lug tops (y 345.5 top, 957.5 bottom), the centre section is longer and runs over the steel end piece to y 372.5 (top) / 930 (bottom); matte, grey level 13..46 (centre section has a soft highlight band near the case: y ~330 top, ~990 bottom); strap outline = alpha silhouette (flares slightly toward the ends, rounded end corners) |
| Steel (lugs, end pieces) | brushed, same as -0001 |

## Decisions

| Decision | Answer |
| --- | --- |
| Strap | `strap.kind = "rubber"` in `config/watches/tudor-bb54-m79000n-0002.json`, built by the own step copy `pipeline/steps/watch_tudor_bb54_rubber.py` (side / centre / side sections, own non-metallic projected-photo material, centre section lifted over the case ramp) |
| Pose, hands, dial | as -0001 (10:09:xx, photo map, 3D hands over the photographed ones) |
| Comparison frame | 2048 px square, camera 27.89 px/mm centred on the pivot (2x photo pivot (902, 1306) at (1024, 1024)), the -0001 preset `config/presets/watch_kit_white_front_tudor_bb54.json` reused read-only |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bb54_prep m79000n-0002   # -> 2x reference, config/watches/tudor-bb54-m79000n-0002-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
