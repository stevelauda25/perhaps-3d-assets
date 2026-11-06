# Reference plan: Seiko Prospex SRPG18J1 (rose gold tone, brown dial, leather strap)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: delivered (round 2, 2026-11-06).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, transparent background, 3306 × 3306 | `front_3306.png` | HAVE, primary for everything |
| 1b | Front, turned toward the crown | `front_turned_3000x4977.png` | Colour reference; not traced (perspective) |
| 2 | Back | none | GAP: not needed for a front relief |
| 3 | 3/4 or side | none | GAP: heights fitted to the listed 11.7 mm |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **42.4 mm** across the flanks (listing). Checks: horn tip to horn tip 44.75 mm traced vs 45.2 listed; strap past the horns 20.31 mm vs 20 listed |
| Colour | Follow the turned SKU photo `front_turned_3000x4977.png` (Irsyad, 2026-11-06): pink rose gold, dark plum-brown dial, maroon insert, dark strap. The photo map from the front photo is graded to it per zone (Lab, `pipeline/seiko_srpg18_dial.py`); crystal base colour black so the dark dial is not hazed in model-viewer |
| Strap | Leather strap with the house curl; its top face uses the photo's own strap (grain, stitching, keeper stitch) |
| Bezel print | Compass letters and ticks stay in the photo map on a raised insert ring |

## Parts

| Part | True shape |
| --- | --- |
| Case | Turtle (cushion) case, brushed top, rounded polished edge, horns either side of the strap |
| Bezel | Coin-edge rose gold ring (about 150 teeth) and a brown insert with N/E/S/W and ticks |
| Dial | Brown, sloped flange with 60 printed ticks, `SEIKO`, Prospex X, `AUTOMATIC 20BAR`, date at 4:30, small print at 6 |
| Indices | Applied rose gold frames with cream lume: trapezoids at 12 (split), 3, 6, 9 with a stick inward; bars elsewhere |
| Hands | Arrow hour hand, sword minute hand (both framed lume), thin seconds hand with a lume lollipop on the tail |
| Crown | Large fluted crown at about 4 o'clock (122.6 deg) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_srpg18_trace   # -> config/watches/seiko-srpg18j1-trace.json
python3 -B -m pipeline.seiko_srpg18_dial    # -> outputs/watches/seiko-srpg18j1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 39.245 px/mm from the 42.4 mm case flanks; origin = hand pivot (1639, 1653) |
| Rings | bezel teeth 20.41/19.65, insert 18.96–15.39, crystal 14.93, dial 13.5 mm |
| Horns | inner edge 10.19 mm, tips 22.75 (12) / 22.0 (6), mean 22.38 mm; case edge between the horns 18.83 mm |
| Hands (10:08:41) | hour 306.4°, 8.6 mm; minute 51.5°, 13.3 mm; seconds 252.5°, 13.1 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-srpg18j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: rose gold turtle case, coin-edge bezel with photo compass insert, framed lume indices and hands, leather strap from the photo with the 7 mm house curl |
| 2 | 2026-11-06 | Colours matched to the turned SKU photo: dial, insert, strap and print graded in the photo map; pinker rose gold; paler lume; black crystal base colour |
