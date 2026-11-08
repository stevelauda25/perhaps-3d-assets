# Reference plan: ROLEX Cosmograph Daytona 126508 green (40 mm yellow gold, green dial, champagne sub-dials, yellow gold tachymetre bezel, three sub-dials, two screw-down pushers, Oyster bracelet in yellow gold)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from the Rolex image host (see `sources.md`). FOLLOWER of the Daytona 40 template (126500LN, `references/rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`): step, prep and kit preset are reused read-only by key `126508green`.

## Target asset

Front relief GLB `models/watches/rolex-126508-green.glb` (the SKU repeats in the tracker, so the variant is part of the name), flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, gold bezel ring with chamfer and polished edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two screw-down pushers, Oyster bracelet links and backing). Gold has no separate material: the steel map (photo projection) carries the colour.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 985 x 1832 px incl. the crown and pushers | `rolex-126508-green_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Checked against the template (same camera)

| Item | Result |
| --- | --- |
| Registration | alpha silhouette of this photo versus the 126500LN photo: 267 px differ out of 1.16 M, leftmost case edge 510.75, case centre x 960.0, pivot (960, 1425), scale 22.4625 px/mm unchanged; the template's kit preset is reused |
| Bracelet | column edges at rows 715 .. 2505 identical to the pixel; joint rows (outer top 770.5, bottom 2159 / 2346 / 2467; centre 2031 / 2040.5 / 2243 / 2422) found at the same rows by edge scans, so the template pieces stay |
| Hands | the render uses the same time (hour 305 deg, minute 62.5 deg, chronograph seconds 323.8 deg); sub-dial needles at the same hubs; traced polygons overlaid at 3.5x on the gold hands fit within about 1 px |
| Per photo | green sunburst dial, champagne sub-dials, gold bezel (not ceramic: `steel.bezel_emission` = steel emission), gold hands with lume, gold bracelet (emission re-tuned) |
