# Reference plan: ROLEX Cosmograph Daytona 126518LN (40 mm yellow gold, champagne dial with black sub-dial rings, black Cerachrom tachymetre bezel, three sub-dials, two gold screw-down pushers, black Oysterflex strap)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). FOLLOWER of the Daytona 40 template (126500LN, see `../rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`; the 126503 follower has the same gold parts): step `pipeline/steps/watch_rolex_daytona40.py`, prep `pipeline/rolex_daytona40_prep.py` and kit preset `config/presets/watch_kit_white_front_rolex_daytona40.json` used read-only. First Daytona with a rubber strap (the 126519LN Oysterflex follows).

## Target asset

Front relief GLB `models/watches/rolex-126518ln.glb`, flat back, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, ceramic bezel ring with chamfer and edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two screw-down pushers, three-column rubber strap and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126518ln_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (continuous px of the native frame)

| Item | Result |
| --- | --- |
| Registration | same camera and scale as the 126500LN template: 22.4625 px/mm, pivot (960.25, 1424.6), case flank left edge 511 (template 510.75); rings, ellipses, crown and pushers kept, checked by overlay |
| Dial | CHAMPAGNE sunray dial, gold-framed applied indices with lume, gold hands, bright black sub-dials with white print, red DAYTONA |
| Bezel | black Cerachrom with the raised tachymetre scale (texture); the white / grey sheen in the render is baked |
| Hands (about 10:09:55, as the template) | hour 305.0 deg, minute 62.5 deg, chronograph seconds 323.8 deg, three gold sub-dial needles; outlines of the template hold (overlay at 2x) |
| Strap | black Oysterflex: flared outer rubber sides (x 732..1188 px, ends row 685 top / 2514 bottom with rounded corners) and a raised centre blade x 858..1060 px (ends row 670.4 top / 2528.4 bottom); column lines measured by gradient maxima (see the spec note); metal lug caps are in the case outline |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126518ln   # -> config/watches/rolex-daytona40-126518ln-trace.json, outputs/watches/rolex-daytona40-126518ln/{dial_photo,steel_photo}.jpg
```
