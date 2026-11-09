# Reference plan: ROLEX Cosmograph Daytona 116519LN (40 mm white gold, steel-grey dial with black sub-dials, black Cerachrom tachymetre bezel, three sub-dials, two white gold screw-down pushers, black Oysterflex strap)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). FOLLOWER of the Daytona 126519LN / 126518LN Oysterflex builds (`../rolex-cosmograph-daytona-126519ln/baseline/BASELINE.md`, `../rolex-cosmograph-daytona-126518ln/baseline/BASELINE.md`, section "Oysterflex strap recipe") and of the 126500LN template: step `pipeline/steps/watch_rolex_daytona40.py` and prep `pipeline/rolex_daytona40_prep.py` used read-only by key; own kit preset `config/presets/watch_kit_white_front_rolex_daytona40_116519.json` because the photo has another camera and scale.

## Target asset

Front relief GLB `models/watches/rolex-116519ln.glb`, flat back, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, ceramic bezel ring with chamfer and edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two screw-down pushers, three-column rubber strap and backing). Only the strap length the photo shows is built.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, retailer render, alpha background, 2880 x 2880 RGBA PNG | `rolex-116519ln_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (continuous px of the native frame)

| Item | Result |
| --- | --- |
| Registration | NOT the Rolex-host camera: 32.0475 px/mm (40 mm flank: left edge 805.75, centre 1446.7), hub / pivot (1445.2, 1213.9), integer pivot (1445, 1214); ceramic outer edge ellipse centre (1446.5, 1228.5), rx 629.1, ry 615.4 (the render is 2 % flatter vertically); ceramic inner edge about r 498 (older case: wider ceramic ring than the 126xxx) |
| Dial | steel-grey sunburst dial, black sub-dials with white print and rings, white-framed lume indices, red DAYTONA, 1/5 s track on the flange, engraved rehaut; sub-dial hubs (1223.4, 1198.5), (1667.2, 1197.5), (1447.8, 1450.5) |
| Hands | white gold hour (299.4 deg) / minute (68.2 deg) / chronograph (327 deg) hands, sub-dial needles measured point by point |
| Case | alpha contour between the horn rows 537 / 2041 (lug to lug 46.9 mm); crown x 2085..2204, y 1144..1352; pushers on axes +-28 deg |
| Strap | black Oysterflex with a raised centre blade; the render cuts it at row 197 (centre blade) / 213 (flared sides) at the top and about 2680 / 2655..2669 at the bottom (slanted cut) |
