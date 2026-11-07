# Reference plan: PATEK PHILIPPE Nautilus 5711/1A (40 mm steel, blue horizontally embossed dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 107 (see `sources.md`). FOLLOWER of the Nautilus template built for the 5811/1G (`../patek-nautilus-5811-1g/baseline/BASELINE.md`); the 5712/1A (row 109, `../patek-nautilus-5712-1a/`) follows this build.

## Target asset

Front relief GLB `models/watches/patek-57111a.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case, bezel with polished outer band and window chamfer, crystal, dial plate, three hands at different heights, hub, crown, bracelet rows, polished centre pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, white background, 350 x 492 JPEG without alpha; the watch is 275 x 459 px incl. the crown (about 6.6 px/mm) | `patek-57111a_original.jpg` | HAVE (untouched; enlarged x4 with Lanczos in memory for measuring and maps; there is no larger version on the host) |
| 2 | Side / back / crown close-up | none | not available; heights are the Nautilus template's, back flat |

## Measured on this photo (continuous px of the x4 working image, 1400 x 1968; one source px = 4 working px)

| Item | Result |
| --- | --- |
| Anchor | listed 40 mm = left flank (mask edge, x about 166 over rows 800..900) to right flank (x about 1225 over rows 740..790 and 935..990): 26.506 working px/mm; the pivot is 7 px right of the case centre |
| Pivot | hub centre (702.0, 853.0); seconds shaft 1.6 px right of it at the pivot row (tilt 0.42 deg) |
| Bezel | rounded-octagon polished outer band 32 px wide, outer outline = superellipse centred (702.5, 860), half axes 472.5 x 476 px, exponent 2.35 (as the 5811), cut back to the silhouette; cushion window scanned on 360 rays (13.3 to 14.4 mm from the pivot), chamfer 10 px |
| Case | "ears" left and right (silhouette), crown shoulder; end links meet the bracelet at rows 322 (top, 20.1 mm) and 1425 (bottom, 21.6 mm) |
| Dial | blue gradient horizontally embossed dial, applied baton indices (12 is a double baton, 6 carries the seconds hand), minute dots, date window at 3, "SWISS" at 6: all in the photo map, soft at 6.6 px/mm |
| Crown | one fluted crown at 3 o'clock, axis row 858, base x 1183 (inside the case), max radius 60 px (2.26 mm), tip x 1257 (a smaller crown than the 5811's) |
| Bracelet | integrated, three columns: brushed outer-link rows (top: joints at y 117, 211, 322; bottom: 1425, 1565, 1703, 1805, end 1880) with polished centre pieces (top 4, bottom 5) that straddle the joints |
| Hands (about 10:08:25) | hour compass 302.6 deg (frame half width 17 px, tip s 207.5), minute 49.48 deg (half 15, tip s 308), seconds 179.6 deg (shaft to the 6 o'clock baton s 317.4, counterweight tail tip s 121); hub discs 30 / 16 px |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | the template's `pipeline/steps/watch_patek_nautilus41.py`, read-only (spec / trace driven) |
| Prep | new `pipeline/patek_nautilus40_prep.py` (variant-named copy of the template prep; adds the two-flank scale anchor and the mask clip for the drop shadow; the 5712/1A reuses it by its key) |
| Comparison frame | 1280 px square at half the working scale (13.2532 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_patek_nautilus40.json`; the compared photo is the x4 working image downscaled by 0.5 (INTER_AREA) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_nautilus40_prep 57111a   # -> config/watches/patek-nautilus40-57111a-trace.json, outputs/watches/patek-nautilus40-57111a/{dial_photo,steel_photo}.jpg
```
