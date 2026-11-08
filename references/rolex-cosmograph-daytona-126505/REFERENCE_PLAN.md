# Reference plan: ROLEX Cosmograph Daytona 126505 (40 mm Everose gold, chocolate dial with black sub-dial rings, Everose bezel with tachymetre scale, three sub-dials, two screw-down pushers, Everose Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Daytona 40 template (`references/rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`): `pipeline/steps/watch_rolex_daytona40.py`, `pipeline/rolex_daytona40_prep.py` and `config/presets/watch_kit_white_front_rolex_daytona40.json` are used read-only by key.

## Target asset

Front relief GLB `models/watches/rolex-126505.glb`, flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, metal bezel ring with chamfer and edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two pushers, Oyster bracelet links and backing). Gold has no separate material: the photo projected on the steel parts carries the Everose colour.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, same camera and scale as the 126500LN render (alpha IoU 0.9995, leftmost case edge 511, hub, rows identical) | `rolex-126505_original.png` | HAVE (untouched, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Observed on this photo

Registration identical to the template (scale 22.4625 px/mm, pivot (960, 1425)). Dial: chocolate brown sunburst, Everose applied baton indices with lume, ROLEX coronet and print in Everose, red DAYTONA, three black sub-dials with Everose rings and needles (12-hour at 9, 30-minute at 3, small seconds at 6). Bezel: Everose, engraved tachymetre scale 65..400 and UNITS PER HOUR in black. Hands: same pose as the template (about 10:09:55), Everose with black facets and lume. Bracelet: Everose Oyster, three columns, same layout as the steel one. The tracker's "chocolate" matches the photo.

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126505   # -> config/watches/rolex-daytona40-126505-trace.json, outputs/watches/rolex-daytona40-126505/{dial_photo,steel_photo}.jpg
```
