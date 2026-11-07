# Reference plan: PATEK PHILIPPE Nautilus 5811/1G (41 mm white gold, blue horizontally embossed dial, white gold bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 111 (see `sources.md`). NEW MODEL: this is the Nautilus template; the steel 5711/1A (row 107) and 5712/1A (row 109, 350 px JPEGs) follow it.

## Target asset

Front relief GLB `models/watches/patek-58111g.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case, bezel with polished outer band and window chamfer, crystal, dial plate, three hands at different heights, hub, crown, bracelet rows, polished centre pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2691 RGBA PNG, the watch is 1401 x 2291 px incl. the crown | `patek-58111g_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights are the Aquanaut template's (case thickness about 8.3 mm real), back flat |

## Measured on this photo (continuous px of the native 1920 x 2691 frame)

| Item | Result |
| --- | --- |
| Anchor | listed 41 mm case = left flank of the case (median alpha edge over rows 1340..1440, x about 271.4) to the right flank (x 1643 at the crown notch); pivot 20.5 mm from the left flank; 33.5615 px/mm |
| Pivot | centre of the small hub screw / dark seconds hub disc (959.4, 1370.0); the seconds tail centre line is at x 960.0, the shaft at x 956.6 at the 6 o'clock baton (camera tilt 0.4 deg) |
| Bezel | rounded-octagon polished outer band of about 40 px, brushed face inside; outer outline = superellipse centred (959.4, 1370), half axes 612 x 608 px, exponent 2.35 (checked on five outline points within 2 %), cut back to the silhouette; cushion window scanned on 360 rays (13.75 to 14.81 mm from the pivot), chamfer 12 px |
| Case | "ears" left and right (silhouette), crown shoulder; top end link meets the bracelet at row 678 (20.5 mm), bottom at row 2087 (21.4 mm) |
| Dial | blue gradient horizontally embossed dial, applied baton indices (12 is a double baton, 6 carries the seconds hand), minute dots, date window at 3, "SWISS" at 6: all in the native photo map, the embossing is texture only |
| Crown | one fluted crown at 3 o'clock, axis y 1380 (10 px below the pivot: camera tilt), radius 84.5 px at x 1646..1653, tip x 1672.5; barrel from x 1600 (radius 59) |
| Bracelet | integrated, three columns: brushed outer-link rows (top: joints at y 377, 521, 678; bottom: 2087, 2245, 2392, 2500, lens end piece 2531..2551) with polished centre pieces (top 4, bottom 5) that straddle the joints; widths follow the silhouette (taper) |
| Hands (about 10:09:30) | hour 304.56 deg (frame half width 22.5 px, lume half 10, round tip s 262), minute 49.44 deg (frame half 19, lume 9, tip s 404), seconds 180.4 deg (shaft half 3.3, tip s 414 at the end of the 6 o'clock baton, spade counterweight tail to s 154); hour-hand base disc radius 38.7 px, seconds hub 20.5 px |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_patek_nautilus41.py` (copy of the Aquanaut step with the bracelet rows / pieces, polished outer band on the bezel) |
| Prep | new `pipeline/patek_nautilus41_prep.py` (copy of the Aquanaut prep; bracelet rows / pieces, steel map cap 2048 px, optional upscale + flood-fill mask for the low-resolution JPEG siblings) |
| Comparison frame | 1280 px square at half the native scale (16.7808 px/mm) centred on the pivot (half-size photo pivot (479.7, 685.0) at (640, 640)), `config/presets/watch_kit_white_front_patek_nautilus41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_nautilus41_prep 58111g   # -> config/watches/patek-nautilus41-58111g-trace.json, outputs/watches/patek-nautilus41-58111g/{dial_photo,steel_photo}.jpg
```
