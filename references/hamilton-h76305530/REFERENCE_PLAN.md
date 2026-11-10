# Reference plan: Hamilton H76305530 (Khaki Aviation Pilot Auto 39 mm, black dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/hamilton-h76305530.glb`, built like `orient-ra-ac0p03l10b.glb`: front relief, flat back, 2.5D depth, modelled case, hands, crown and lugs in house steel and glass, strap with the house curl; the dial and the strap leather from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1714 × 2610 | `front_1714x2610.jpg` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the official 11.6 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Official | Measured at 39 mm (36.25 px/mm) |
| --- | --- | --- |
| Case width | **39 mm** (anchor) | circle fitted to the flanks, centred 0.28 mm right and 0.15 mm below the hand pivot (807, 1226) |
| Bezel | not listed | brushed flat ring 34.8-39 mm; polished inner bevel 33.2-34.8 mm; chapter ring 28.6-33.2 mm |
| Lug width | 20 mm | lug gap 19.5 mm; strap 19.0-19.4 mm |
| Lug to lug | not listed | 45.1 mm (tips 21.8 mm top, 23.3 mm bottom: the photo is not centred on the pivot), used symmetric |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Brushed round case, wide flat brushed bezel, polished inner bevel | #1; rings read along rays |
| Dial | Matte black; printed 05-55 and 1-12, triangle at 12, bars at 3 6 9, grey chapter ring with minute marks and 5-minute blocks, star logo, HAMILTON, AUTOMATIC, SWISS MADE | dial map |
| Hands | Sword hands with a polished outline and lume body; the hour tip and the minute root are open skeletons; polished paddle tails. Seconds: polished needle, lume arrow, polished ring on the tail | #1, bright components in hand-aligned crops |
| Crown | Large fluted crown at 3 with a rounded end | #1 |
| Lugs | Straight lugs, outline from the silhouette | #1 |
| Strap | Brown leather, edge stitching, embossed logo on the bottom piece | strap map, each side from its own photo strap |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 39 mm case width (official); the lug gap then measures 19.5 mm against 20 mm |
| Printed markers | The numerals, triangle and bars are printed lume in the photo: dial map, no geometry |
| Heights | Front-relief reading of the official 11.6 mm (no side photo) |
| Hand pose | The pose in #1 (about 10:09:32) |
| Strap curve | House curl: 7 mm radius from the lug tips, 2.2 R of arc |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h76305530_trace   # -> config/watches/hamilton-h76305530-trace.json
python3 -B -m pipeline.hamilton_h76305530_dial    # -> outputs/watches/hamilton-h76305530/dial_photo.jpg and strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
