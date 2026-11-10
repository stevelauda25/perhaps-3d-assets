# Reference plan: Orient FAC0000EW0 (Bambino version 3, white dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied an angled photo only; the straight-on front is Orient USA's image of TAC0000EW0, the US code of the same watch.

## Target asset

A front-facing GLB in `models/watches/orient-fac0000ew0.glb`, built like `orient-ra-ac0f06l10b.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, domed crystal, lugs, crown, applied batons and hands in house steel and glass; photo maps for the dial print and the leather strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, Orient USA, 1600 × 1067 (2× copy, rectified 3200 × 2223) | `front_orientusa_1600x1067.png`, `front_2x_rect_3200x2223.png` | HAVE, primary; shot a little from below, so stretched 1.0416× vertically until the dial ring is round |
| 2 | 3/4 from the crown side | `three_quarter_orientusa.png`, `angled_1000x1588.jpg` | HAVE, case, bezel and dome shape by eye |
| 3 | Back | none | not needed |

## Scale anchors

| Dimension | Listed | Measured at 40.5 mm (32.07 px/mm on the rectified copy) |
| --- | --- | --- |
| Case width | **40.5 mm** (anchor, listings) | flanks at 3 and 9 |
| Lug to lug | 46.5 mm | 46.4 mm after the stretch |
| Lug width | 21 mm | strap 21.3-22.4 mm in the photo (the strap widens a little past the lugs) |
| Crystal ring | not listed | 36.7 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, bezel | Polished round case, thin bezel sloping in to a domed crystal | #1, #2 |
| Dial | White, printed hour lines at 1 2 4 5 7 8 10 11, minute track, logo, Water Resistant | dial map |
| Indices | Applied faceted rectangular batons at 12 3 6 9 (the 3 starts further out beside the date) | #1 |
| Hands | Flat-ended faceted baton hour and minute hands; thin seconds needle with a short tail | #1 |
| Crown | Fluted with a smooth end cap | #1 |
| Strap | Dark brown leather, contrast stitching, 21 mm | strap map from the 12 o'clock strap (the 6 o'clock one is in deep shadow) |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Orient USA image of TAC0000EW0, rectified |
| Scale | 40.5 mm case; lug tips at 23.25 mm (listed 46.5 mm) |
| Hand pose | The pose in #1 (about 10:08:35) |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_fac0000ew0_trace   # -> config/watches/orient-fac0000ew0-trace.json
python3 -B -m pipeline.orient_fac0000ew0_dial    # -> outputs/watches/orient-fac0000ew0/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
