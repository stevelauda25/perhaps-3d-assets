# Reference plan: ROLEX Cosmograph Daytona 126506A (40 mm platinum, ice blue diamond dial, brown ceramic bezel, three sub-dials, two screw-down pushers, platinum Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo from the Rolex image host (see `sources.md`). FOLLOWER of the Daytona 40 template (`../rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`): step, prep and kit preset are reused read-only by key `126506a`.

## Target asset

Front relief GLB `models/watches/rolex-126506a.glb`, flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, bezel ring with chamfer and polished edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two pushers, Oyster bracelet links and backing). The diamond indices are part of the dial photo map (no separate 3D parts, as the template's applied indices); platinum colour comes through the projected photo.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126506a_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Daytona template, back flat |

## Measured on this photo

| Item | Result |
| --- | --- |
| Registration | same camera as the template: leftmost alpha edge 511, alpha silhouettes differ by 265 px; scale 22.4625 px/mm, pivot int (960, 1425) |
| Dial | ICE BLUE sunburst, eight baguette diamonds (1, 2, 4, 5, 7, 8, 10, 11) and square-cut diamonds at 9, 3, 6, ROLEX coronet, OYSTER PERPETUAL, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, COSMOGRAPH, red DAYTONA, three brown-ringed sub-dials, SWISS MADE at 6 |
| Bezel | brown Cerachrom with white-engraved tachymetre scale 60..400 and UNITS PER HOUR (texture) |
| Hands | same time as the template (~10:09:55): platinum swords with lume strip, white chronograph needle with arrow head and paddle tail, platinum sub-dial needles; minute hand tip re-picked (the template's wing was the white dial's index) |
| Bracelet | platinum Oyster, three columns, joints checked against the template rows |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep / kit preset | `pipeline/steps/watch_rolex_daytona40.py`, `pipeline/rolex_daytona40_prep.py <key>`, `config/presets/watch_kit_white_front_rolex_daytona40.json` (all read-only; key 126506a) |
| Per photo | `config/watches/rolex-daytona40-126506a{,-measure,-trace}.json`, `jobs/rolex-daytona40-126506a.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126506a   # trace, dial_photo.jpg, steel_photo.jpg
```
