# Reference plan: ROLEX Cosmograph Daytona 126508 yellow (40 mm 18 ct yellow gold, champagne dial with black sub-dial rings, yellow gold bezel with engraved tachymetre scale, three sub-dials, two screw-down pushers, Oyster bracelet in yellow gold)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Daytona 40 template (`../rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`): step, prep and kit preset are reused read-only by key.

## Target asset

Front relief GLB `models/watches/rolex-126508-yellow.glb` (variant in the name because the SKU repeats), flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, bezel ring with chamfer and polished edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two pushers, Oyster bracelet links and backing). Gold parts have no separate material: the colour comes through the projected photo.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126508-yellow_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Daytona template, back flat |

## Measured on this photo

| Item | Result |
| --- | --- |
| Registration | same camera as the template: leftmost alpha edge 511 at rows 1436..1440, alpha silhouettes differ by 426 px, so scale 22.4625 px/mm, pivot int (960, 1425) |
| Dial | CHAMPAGNE (light gold sunburst) dial, applied gold baton indices with lume, ROLEX coronet, OYSTER PERPETUAL, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, COSMOGRAPH, red DAYTONA, three black-ringed sub-dials (9, 3, 6) with gold needles |
| Bezel | yellow gold, engraved black tachymetre scale (60..400 units per hour) and UNITS PER HOUR: texture (not ceramic; the tracker's row is the gold-bezel model) |
| Hands | same time as the template (about 10:09:55): gold swords with black facet and white lume strip, gold chronograph seconds needle with arrow head, gold sub-dial needles; checked by overlay |
| Bracelet | Oyster, three columns, gold; joints checked against the template's rows |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep / kit preset | `pipeline/steps/watch_rolex_daytona40.py`, `pipeline/rolex_daytona40_prep.py <key>`, `config/presets/watch_kit_white_front_rolex_daytona40.json` (all read-only; key 126508yellow) |
| Per photo | `config/watches/rolex-daytona40-126508yellow{,-measure,-trace}.json`, `jobs/rolex-daytona40-126508yellow.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126508yellow   # trace, dial_photo.jpg, steel_photo.jpg
```
