# Reference plan: Hamilton H69439940 (Khaki Field Mechanical 38 mm, blue dial, blue NATO strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
the straight front photo. House method: modelled case, bezel, lugs, crown, hub and hands in house steel, paint, lume and
glass; photo maps only for the dial print and the NATO strap. Build step `watch_hamilton_h69439940` (shared with H70405710).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1869 × 2909 | `front_1869x2909.jpg` | HAVE, primary for everything |
| 2 | 3/4, back, side | none | GAP: heights estimated from the official 9.5 mm |

## Scale anchors

| Dimension | Official / listed | Measured at 38 mm (35.57 px/mm) |
| --- | --- | --- |
| Case diameter | **38.0 mm** (anchor) | 9-3 row, case edge to the crown root |
| Strap | 20 mm (official lug width) | 20.2-20.5 mm past the lug tips |
| Lug to lug | 47 mm (reviews) | 46.7 mm (top lugs 1.1 mm shorter: photo taken a little from below) |
| Crystal ring | not listed | 33.1 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, bead-blasted, ridge at r 18.3 mm, wide sloped blasted bezel to the crystal | #1 |
| Lugs | Straight blasted lugs, flat square ends, outer edge widening into the case | #1 silhouette |
| Dial | Blue sunburst, printed white 12-hour and 24-hour numerals, minute track, cream lume triangles, HAMILTON, SWISS MADE | dial map |
| Hands | White painted pencil hour and minute with cream lume, white seconds with a lume arrow and a round counterweight, white boss | #1, gridded crops |
| Crown | Fluted (24), blasted, smooth rounded end, at 3 | #1 |
| Strap | Blue NATO, 20 mm | strap map (bottom strap) |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | Official 38 mm case, listed 47 mm lug to lug |
| Centre | Hand pivot; the case circle centre is within 1 px |
| Finish | Bead-blasted matte steel (roughness 0.42) instead of the house polished steel: the photo's case is matte |
| Hidden print | Print under the hands (end of HAMILTON, part of 22) is not rebuilt: the 3D hands sit at the photo's time and cover it |
| Heights | Front-relief reading of the official 9.5 mm; bezel slope direction inferred |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |
| NATO buckle | Beside the top strap in the photo; not modelled |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h69439940_trace   # -> config/watches/hamilton-h69439940-trace.json
python3 -B -m pipeline.hamilton_h69439940_dial    # -> outputs/watches/hamilton-h69439940/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Delivered to `models/watches/hamilton-h69439940.glb` |
