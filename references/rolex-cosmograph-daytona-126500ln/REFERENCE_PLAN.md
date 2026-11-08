# Reference plan: ROLEX Cosmograph Daytona 126500LN (40 mm steel, white dial with black sub-dial rings, black Cerachrom tachymetre bezel, three sub-dials, two screw-down pushers, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL: the Daytona 40 template, adapted from the GMT-Master II 40 / Submariner Date 41 builds (ceramic bezel, free-polygon hands, Oyster bracelet columns, specs / jobs / presets) and the chronograph builds (Tudor Black Bay Chrono, Omega Moonwatch: sub-dial hubs, angled pushers). The other eight Daytona rows (126503, 126505, 126518LN, 126508 yellow / green, 126519LN, 126506, 126506A) follow.

## Target asset

Front relief GLB `models/watches/rolex-126500ln.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, ceramic bezel ring with chamfer and polished edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two screw-down pushers, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 986 x 1832 px incl. the crown and pushers | `rolex-126500ln_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Submariner / GMT-Master II templates, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | scale 22.4625 px/mm (40 mm = case flank diameter: leftmost alpha edge 510.75 at rows 1436..1440, case centre x 960.0), pivot = hub screw (960.25, 1424.6) -> int (960, 1425); rings (px, about the hub): dial 322.5, flange / crystal edge 351, bezel inner edge 361.7, ceramic start 383.3, ceramic outer edge ellipse (centre 959.6, 1432.3; rx 441.8, ry 435.3), case flank ellipse (centre 960, 1437; rx 449.25, ry 442.5): the render is about 1.5 % flatter vertically at the bezel |
| Dial | WHITE dial, applied baton indices with lume, ROLEX coronet, OYSTER PERPETUAL, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, COSMOGRAPH, red DAYTONA, minute track (the tracker's "white or black": this photo is the white dial with black sub-dial rings), three black-ringed sub-dials (12-hour counter at 9, 30-minute counter at 3, small seconds at 6) with their own needles and hub discs (r 14.8 px = 0.66 mm) |
| Bezel | black Cerachrom, raised platinum tachymetre scale (65..400 units per hour) and UNITS PER HOUR: texture; the glossy reflection on the left and bottom is baked in the render |
| Hands (about 10:09:55) | hour 305.0 deg sword (black facet + lume strip), minute 62.5 deg sword with a lume wing, chronograph seconds 323.8 deg (needle with arrow head and paddle tail), sub-dial needles; picked as [s, w] polygons / px polygons |
| Crown / pushers | crown axis y 1436 (0.49 mm below the pivot), fluted body x 1405..1472, cap to 1496.5, radius 77 px (3.43 mm); pushers radial from (963.4, 1437) at +-28 deg: neck r 55.5 px, fluted ring r 61.9 px (s 475..513), cap r 43.5 px to s 547.5 |
| Case | horns y 910 (22.93 mm) and 1990 (25.15 mm), crown guards and pusher barrels in the alpha contour |
| Bracelet | Oyster, three columns: outer brushed links with rounded ends, polished centre links; column lines x 861 / 1058 (top), 860 / 1060 (bottom); joints in `config/watches/rolex-daytona40-126500ln.json` (`strap.bracelet.note`); ends y 682 (top) and 2513.6 (bottom) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_daytona40.py` (copy of the GMT-Master II 40 step: case = photo contour, fixed ceramic bezel, polygon hands incl. sub-dial hands, crown + two pushers, any column layout) |
| Prep | `pipeline/rolex_daytona40_prep.py <key>` (copy of the GMT-Master II 40 prep: contour outline, hand pivot, ellipses, crown / pushers / sub-dial discs in mm) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_daytona40.json` (own: 11.23125 px/mm) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126500ln   # -> config/watches/rolex-daytona40-126500ln-trace.json, outputs/watches/rolex-daytona40-126500ln/{dial_photo,steel_photo}.jpg
```
