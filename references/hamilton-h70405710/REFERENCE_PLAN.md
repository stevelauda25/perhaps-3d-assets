# Reference plan: Hamilton H70405710 (Khaki Field Murph 38 mm, white dial, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
the straight front photo. House method: modelled case, bezel, lugs, crown, hub and hands in house steel, lume and glass;
photo maps only for the dial print and the leather strap. Build step `watch_hamilton_h69439940` (shared with H69439940).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1650 × 2539 | `front_1650x2539.jpg` | HAVE, primary for everything |
| 2 | 3/4, back, side | none | GAP: heights estimated from the listed 11.1 mm |

## Scale anchors

| Dimension | Official / listed | Measured at 38 mm (35.10 px/mm) |
| --- | --- | --- |
| Case diameter | **38.0 mm** (anchor) | 9-3 row, case edge to the crown root |
| Strap | 20 mm (lug width) | 19.5 mm past the lug tips, tapering to 17.9 mm |
| Lug to lug | 44.7 mm (retailers) | 44.0 mm (lugs curve down: foreshortened) |
| Crystal ring | not listed | 32.9 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, brushed flank with a narrow flat top, wide polished bezel curving up to the crystal | #1 |
| Lugs | Brushed lugs with polished edges, slanted bent-down ends | #1 silhouette |
| Dial | White, printed black minute track with seconds numerals, cream lume Arabic numerals with black outlines, HAMILTON, KHAKI AUTOMATIC, SWISS MADE | dial map |
| Hands | Polished leaf hour hand (four lume petals, thin point), minute sword with three lume segments and a needle point, thin seconds needle, stepped hub | #1, gridded crops |
| Crown | Fluted (26), polished, smooth rounded end, at 3 | #1 |
| Strap | Black croc-pattern leather with white stitching, 20 mm | strap map (bottom strap) |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | Official 38 mm case, listed 44.7 mm lug to lug |
| Centre | Hand pivot |
| Hidden print | Where a needle crosses a numeral (the 10, the 4) the cut is inpainted from the strokes around it; print under wider hand parts is covered by the 3D hands |
| Crystal | Domed sapphire built as a flat disc at its mean height |
| Heights | Front-relief reading of the listed 11.1 mm |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h70405710_trace   # -> config/watches/hamilton-h70405710-trace.json
python3 -B -m pipeline.hamilton_h70405710_dial    # -> outputs/watches/hamilton-h70405710/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Delivered to `models/watches/hamilton-h70405710.glb` |
