# Reference plan: ROLEX Air-King 126900 (40 mm steel, black dial, domed polished bezel, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from the Rolex image host (see `sources.md`; Catalog 2 tracker position 38). NEW MODEL: this is the Rolex Air-King template (round Oyster case, domed polished bezel, Oyster bracelet); a sibling builds the Oyster Perpetual 41 green at the same time from its own files.

## Target asset

Front relief GLB `models/watches/rolex-126900.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, domed bezel with window chamfer, crystal, dial plate, three hands at different heights, hub, crown, bracelet rows, centre-link pieces).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 992 x 1828 px incl. the crown | `rolex-126900_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Nautilus template (back flat) |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | listed 40 mm case = left flank (median alpha edge over rows 1400..1470, x 507.5) to the pivot 20 mm: 22.5861 px/mm; the crown notch (right flank, hidden behind the crown barrel) is x 1408 = 19.9 mm |
| Pivot | centre of the hub (959.2, 1425.0); the hour / minute / seconds axes pass 3 / 2 / 0.6 px off it (camera tilt), kept inside the traced outlines |
| Bezel | domed polished, outer ellipse centre (959.4, 1427.5) half axes 452 x 445 px (left silhouette, radial gradient edge at 12 / 6 o'clock); inner edge a circle centre (958.8, 1421.3) r 392.4 px (fitted to 720 radial edge scans, std 2.5 px); polished highlights and the black reflection at 1 to 2 o'clock are texture |
| Case | lugs top end at the outer-link joint y 917 (22.5 mm), bottom end y 1986 (24.8 mm); crown guards above (rows 1290..1357) and below (rows 1519..1620) stay in the silhouette; crown barrel x 1408..1470, y 1358..1514, domed cap to x 1498, axis y 1436 |
| Dial | black dial, applied white-framed Arabic numerals 3 / 6 / 9 and minute numerals, white triangle at 12, green ROLEX with yellow crown, "OYSTER PERPETUAL", "Air-King" script, "SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED", SWISS MADE; minute track and rehaut ring: all in the native photo map |
| Hands (10:09:30) | hour 304.6 deg (Mercedes disc, arrowhead tip s 201.5 px), minute 63.1 deg (tip 319.5 px), seconds 186.1 deg (green, lume ring r 21 at s 182, head disc, tip 333.5); hub r 25 / 19.5 px |
| Bracelet | Oyster, three columns: brushed outer-link rows (top: joints y 760, 917; bottom: 1986 (lug end), 2184, 2364, 2483, end 2514) and centre links (top joints 729, 865; bottom 2058, 2262, 2409, 2500); widths follow the silhouette (taper) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_rolex_airking.py` (copy of the Nautilus step: domed bezel ring, hands from traced outlines) |
| Prep | new `pipeline/rolex_airking_prep.py` (copy of the Nautilus prep: fitted-circle window edge, hand outline polygons, Rolex file names) |
| Comparison frame | 1280 px square at half the native scale (11.2931 px/mm) centred on the pivot (half-size photo pivot (479.6, 712.5) at (640, 640)), `config/presets/watch_kit_white_front_rolex_airking.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_airking_prep 126900   # -> config/watches/rolex-airking-126900-trace.json, outputs/watches/rolex-airking-126900/{dial_photo,steel_photo}.jpg
```
