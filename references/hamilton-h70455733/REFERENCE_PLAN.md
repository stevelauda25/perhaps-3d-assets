# Reference plan: Hamilton H70455733 (Khaki Field Auto 38 mm, black dial with date, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
a 3/4 photo only; the straight front is Hamilton's official product render (Bucherer listing, see `sources.md`). House
method: modelled case, bezel, lugs, crown, date frame, hub and hands in house steel, paint, lume and glass; photo maps only
for the dial print and the leather strap. Build step `watch_hamilton_h69439940` (shared with H69439940).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, official render, 2100 × 2054 | `front_2100x2054.png` (+ white copy) | HAVE, primary for everything |
| 2 | 3/4 from the crown side | `three_quarter_1000x1546.jpg` | HAVE (supplied) |
| 3 | Angled close-up | `angled_800x800.jpg` | HAVE: bezel slope by eye |
| 4 | Side, back | none | GAP: heights estimated from the official 11 mm |

## Scale anchors

| Dimension | Official | Measured at 38 mm (23.78 px/mm) |
| --- | --- | --- |
| Case diameter | **38.0 mm** (anchor) | 9-3 row, case edge to the mirrored right edge |
| Lug to lug | 47 mm | 47.3 mm |
| Strap | 20 mm | 19.8 mm past the lug tips, tapering to 18.0 mm |
| Crystal ring | not listed | 33.7 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, brushed flank with a narrow flat top, wide polished bezel curving up to the crystal | #1, #3 |
| Lugs | Brushed lugs with polished edges, rounded ends | #1 silhouette |
| Dial | Black, white 12-hour and 24-hour numerals, minute track with dots and seconds numerals, sunburst inner zone, HAMILTON, KHAKI AUTOMATIC, date at 3 | dial map |
| Date | Applied polished frame; the window and its numeral stay in the dial map | #1 |
| Hands | Polished pencil hour and minute with pale lume and thin needle points, white seconds with a small counterweight disc and a red arrow tip, stepped hub | #1, straightened crops |
| Crown | Fluted (22), polished, smooth end, at 3 | #1 |
| Strap | Black leather with light stitching, 20 mm | strap map (bottom strap) |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Hamilton's official render (the supplied photo is 3/4 only) |
| Scale | Official 38 mm case and 47 mm lug to lug |
| Dial clean-up | Inside the minute track the hand zones are inpainted from the plain black dial (6 deg copies dragged the hand edges in); the track is copied 6 deg over |
| Heights | Front-relief reading of the official 11 mm |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h70455733_trace   # -> config/watches/hamilton-h70455733-trace.json
python3 -B -m pipeline.hamilton_h70455733_dial    # -> outputs/watches/hamilton-h70455733/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Delivered to `models/watches/hamilton-h70455733.glb` |
