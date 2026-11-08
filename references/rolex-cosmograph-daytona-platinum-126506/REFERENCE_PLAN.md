# Reference plan: ROLEX Cosmograph Daytona 126506 (40 mm 950 platinum, ice-blue dial with brown sub-dial rings and baton indices, brown Cerachrom bezel with engraved tachymetre scale, three sub-dials, two screw-down pushers, platinum Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Daytona 40 template (`../rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`): step, prep and kit preset are reused read-only by key `126506`.

## Target asset

Front relief GLB `models/watches/rolex-126506.glb`, flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, bezel ring with chamfer and polished edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two pushers, Oyster bracelet links and backing). Platinum parts have no separate material: the colour comes through the projected photo.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126506_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Daytona template, back flat |

## Measured on this photo

| Item | Result |
| --- | --- |
| Registration | same camera as the template: leftmost alpha edge 511 at rows 1436..1440, alpha silhouettes differ by 265 px, so scale 22.4625 px/mm, pivot int (960, 1425) |
| Dial | ICE-BLUE (light blue sunburst) dial, applied white-gold-tone baton (stick) indices with lume, ROLEX coronet, OYSTER PERPETUAL, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, COSMOGRAPH, red DAYTONA, three BROWN-ringed sub-dials (9, 3, 6) with platinum needles |
| Bezel | brown Cerachrom with engraved platinum-tone tachymetre scale (60..400 units per hour) and UNITS PER HOUR: texture. The ceramic shows a lighter reflection band left and right (photo) |
| Hands | same time as the template (about 10:09:55): platinum swords with lume strip, chronograph seconds needle with arrow head, sub-dial needles; checked by 3x overlay |
| Bracelet | platinum Oyster, three columns; joints checked against the template's rows |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep / kit preset | `pipeline/steps/watch_rolex_daytona40.py`, `pipeline/rolex_daytona40_prep.py <key>`, `config/presets/watch_kit_white_front_rolex_daytona40.json` (all read-only; key 126506) |
| Per photo | `config/watches/rolex-daytona40-126506{,-measure,-trace}.json`, `jobs/rolex-daytona40-126506.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126506   # trace, dial_photo.jpg, steel_photo.jpg
```
