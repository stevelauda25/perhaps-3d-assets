# Reference plan: Hamilton H69439363 (Khaki Field Mechanical 38 mm, green dial with date, green canvas strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
a small, slightly turned photo; the straight front is Hamilton's official product render (Bucherer listing, see
`sources.md`). House method: modelled case, bezel, lugs, crown, date frame, hub and hands in house steel, lume and glass;
photo maps only for the dial print and the canvas strap. Build step `watch_hamilton_h69439940` (shared with H69439940).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, official render, 2100 × 2054 | `front_2100x2054.png` (+ white copy) | HAVE, primary for everything |
| 2 | Near-front (supplied), 900 × 900 | `supplied_900x900.jpg` | HAVE: cross-check only |
| 3 | Angled close-up | `angled_800x800.jpg` | HAVE: bezel slope by eye |
| 4 | Side, back | none | GAP: heights estimated from the official 9.5 mm |

## Scale anchors

| Dimension | Official | Measured at 38 mm (23.63 px/mm) |
| --- | --- | --- |
| Case diameter | **38.0 mm** (anchor) | 9-3 row, case edge to the mirrored right edge |
| Lug to lug | 47 mm | 45.4 mm (the render draws the lug ends short and rounded; official value used) |
| Strap | 20 mm | 19.9 mm past the lug tips |
| Crystal ring | not listed | 32.7 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, bead-blasted, ridge at r 18.2 mm, wide sloped blasted bezel to the crystal | #1, #3 |
| Lugs | Straight blasted lugs, rounded ends | #1 silhouette |
| Dial | Matte green, light 12-hour and 24-hour numerals, minute track with triangles, HAMILTON, KHAKI MECHANICAL, SWISS MADE, date at 3 | dial map |
| Date | Applied polished frame; the window and its numeral stay in the dial map | #1 |
| Hands | Polished pencil hour and minute with off-white lume, polished seconds with a round counterweight and a lume-filled arrow, stepped hub | #1, straightened crops |
| Crown | Fluted (24), blasted, smooth rounded end, at 3 | #1 |
| Strap | Green canvas, 20 mm | strap map (bottom strap) |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Hamilton's official render (the supplied photo is small and turned) |
| Scale | Official 38 mm case and 47 mm lug to lug |
| Dial clean-up | Inside the minute track the hand zones (with their soft drop shadows) are inpainted from the plain green dial; the track is copied 6 deg over |
| Heights | Front-relief reading of the official 9.5 mm; bezel slope direction inferred |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h69439363_trace   # -> config/watches/hamilton-h69439363-trace.json
python3 -B -m pipeline.hamilton_h69439363_dial    # -> outputs/watches/hamilton-h69439363/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Delivered to `models/watches/hamilton-h69439363.glb` |
