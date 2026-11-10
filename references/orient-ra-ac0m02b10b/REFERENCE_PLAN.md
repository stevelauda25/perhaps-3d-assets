# Reference plan: Orient RA-AC0M02B10B (Bambino 38, black dial, black croc leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied an angled photo only; the straight-on front is Orient USA's image of RA-AC0M02B30B, the same watch.

## Target asset

A front-facing GLB in `models/watches/orient-ra-ac0m02b10b.glb`, built like `orient-ra-ac0f06l10b.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, domed crystal, lugs, crown, applied markers and hands in house steel and glass; photo maps for the dial print and the leather strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, Orient USA, 1600 × 1067 (2× copy on white 3200 × 2134) | `front_orientusa_1600x1067.png`, `front_2x_white_3200x2134.png` | HAVE, primary; the case reads round |
| 2 | 3/4 | `three_quarter_orientusa.jpg`, `angled_1200x1200.jpg` | HAVE, case, bezel and dome shape by eye |
| 3 | Back | none | not needed |

## Scale anchors

| Dimension | Listed | Measured at 38.4 mm (33.07 px/mm on the 2× copy) |
| --- | --- | --- |
| Case width | **38.4 mm** (anchor, listings) | flanks at 3 and 9; height also 38.4 mm |
| Lug to lug | 44 mm | 43.7 mm |
| Lug width | 20 mm | strap 19.9-20.2 mm |
| Crystal ring | not listed | 33.3 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, bezel | Polished round case, sloped bezel, domed crystal | #1, #2 |
| Dial | Gloss black with a lighter centre, printed minute track, logo, Water Resistant, movement print | dial map |
| Markers | Applied faceted lancets with a pointed outer end; a pair at 12; a short one beside the date at 3 | #1 |
| Hands | Faceted dauphine hour and minute hands with pointed counter-tails; thin seconds needle with a long tail | #1 |
| Crown | Fluted with a smooth end cap | #1 |
| Strap | Black croc-grain leather, 20 mm | strap map from the 6 o'clock strap |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Orient USA image of RA-AC0M02B30B |
| Scale | 38.4 mm case; lug tips at 22.0 mm (listed 44 mm) |
| Hand pose | The pose in #1 (about 10:09:39) |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0m02b10b_trace   # -> config/watches/orient-ra-ac0m02b10b-trace.json
python3 -B -m pipeline.orient_ra_ac0m02b10b_dial    # -> outputs/watches/orient-ra-ac0m02b10b/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
