# Reference plan: PATEK PHILIPPE Nautilus 5712/1A (40 mm steel, blue horizontally embossed dial with moon phase, power reserve and date, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 109 (see `sources.md`). FOLLOWER of the Nautilus template built for the 5811/1G (`../patek-nautilus-5811-1g/baseline/BASELINE.md`) and followed on the 5711/1A (`../patek-nautilus-5711-1a/baseline/BASELINE.md`).

## Target asset

Front relief GLB `models/watches/patek-57121a.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case, bezel with polished outer band and window chamfer, crystal, dial plate, two hands at different heights, hub, crown, bracelet rows, polished centre pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, white background, 350 x 480 JPEG without alpha; the watch is 271 x 458 px incl. the crown (about 6.6 px/mm) | `patek-57121a_original.jpg` | HAVE (untouched; enlarged x4 with Lanczos in memory for measuring and maps; there is no larger version on the host) |
| 2 | Side / back / crown close-up | none | not available; heights are the Nautilus template's, back flat |

## Measured on this photo (continuous px of the x4 working image, 1400 x 1920; one source px = 4 working px)

| Item | Result |
| --- | --- |
| Anchor | listed 40 mm = left flank (mask edge, x 177 over rows 840..1000) to right flank (x 1229 over rows 760..830 and 985..1040): 26.312 working px/mm |
| Pivot | intersection of the hour and minute lume centre lines (700.4, 887.3), rounded (700.5, 887.5); the hub disc centre (702, 889.5) is 2.7 px away |
| Bezel | rounded-octagon polished outer band 32 px wide, outer outline = superellipse centred (702, 890), half axes 455 x 469 px, exponent 2.35 (as the template), cut back to the silhouette; cushion window scanned on 360 rays (12.7 to 14.2 mm from the pivot), chamfer 10 px |
| Case | "ears" left and right (silhouette), crown shoulder; end links meet the bracelet at rows 354 (top, 20.3 mm) and 1459.5 (bottom, 21.75 mm) |
| Dial | blue gradient horizontally embossed dial, applied baton indices (12 is a double baton), minute dots, power-reserve sub-dial and needle at 9, moon-phase aperture with retrograde date arc and its own pointer at 7, small seconds sub-dial at 4:30, date marker aperture at 6, red date marker, "PATEK PHILIPPE" / "GENEVE": all in the photo map, soft at 6.6 px/mm |
| Crown | one fluted crown at 3 o'clock, axis row 906, base x 1188, max radius 66 px (2.5 mm), tip x 1263 |
| Bracelet | integrated, three columns: brushed outer-link rows (top: joints at y 184.5, 266.5, 354; bottom: 1459.5, 1570, 1663, 1734.5, end 1818 with a rounded bulge to 1834) with polished centre pieces (top 5, bottom 6) |
| Hands (about 10:08) | hour compass 302.2 deg (tip s 207.3, half width 16 px), minute 53.5 deg (tip s 310.0, half width 13 px); no central seconds hand; hub disc 30 px |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_patek_nautilus40_5712.py` = the template step with a hand loop over the hands present (hour, minute): the sub-dial needles stay in the dial map |
| Prep | `pipeline/patek_nautilus40_5712_prep.py` = the 5711/1A prep plus `mask.union_bezel_outer` (silhouette leak into the white polished band) and a hand loop over the measure keys |
| Comparison frame | 1280 px square at half the working scale (13.1562 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_patek_nautilus40_5712.json`; the compared photo is the x4 working image downscaled by 0.5 (INTER_AREA) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_nautilus40_5712_prep 57121a   # -> config/watches/patek-nautilus40-57121a-trace.json, outputs/watches/patek-nautilus40-57121a/{dial_photo,steel_photo}.jpg
```
