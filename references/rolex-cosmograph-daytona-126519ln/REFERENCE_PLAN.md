# Reference plan: ROLEX Cosmograph Daytona 126519LN (40 mm white gold, light grey meteorite dial with black sub-dials, black Cerachrom tachymetre bezel, three sub-dials, two white gold screw-down pushers, black Oysterflex strap)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). FOLLOWER of the Daytona 126518LN (same Oysterflex strap and camera; `../rolex-cosmograph-daytona-126518ln/baseline/BASELINE.md`, section "Oysterflex strap recipe") and of the 126500LN template (`../rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`): step `pipeline/steps/watch_rolex_daytona40.py`, prep `pipeline/rolex_daytona40_prep.py` and kit preset `config/presets/watch_kit_white_front_rolex_daytona40.json` used read-only.

## Target asset

Front relief GLB `models/watches/rolex-126519ln.glb`, flat back, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, ceramic bezel ring with chamfer and edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two screw-down pushers, three-column rubber strap and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126519ln_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (continuous px of the native frame)

| Item | Result |
| --- | --- |
| Registration | same camera and scale: 22.4625 px/mm, pivot (960.25, 1424.6); alpha silhouette differs from the 126518LN one by 38 px, so the strap layout (outer sides to rows 685 / 2514, centre blade to 670.4 / 2528.4), rings, ellipses, crown and pushers are kept and checked by overlay |
| Dial | light grey METEORITE dial (Widmanstaetten pattern is in the dial map), white-framed lume indices, bright black sub-dials with white print, red DAYTONA; a light (not dark) dial |
| Bezel | black Cerachrom with the raised tachymetre scale (texture); white / grey sheen baked |
| Hands | white gold hour / minute / chronograph hands on the light dial, time 10:09:55 as the siblings; overlay of the template outlines at 2x agrees; sub-dial needles and hubs agree |
| Strap | black Oysterflex, same flared outer sides and raised centre blade as the 126518LN |
