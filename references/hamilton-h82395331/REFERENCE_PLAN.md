# Reference plan: Hamilton Khaki Navy Scuba Auto H82395331 (black and orange dial, black diver's bezel, orange rubber strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method:
modelled brushed case, lugs and crown guards, polished coin-edge bezel and crown, applied indices and hands; photo maps only for
the dial print with the bezel insert, and for the rubber strap. File name `hamilton-h82395331`.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1786 × 2751 | `front_1786x2751.jpg` | HAVE, primary for everything (supplied by Irsyad). Under the 2000 px target on the short side |
| 2 | 3/4 from the crown side | none | GAP: heights are the house values scaled to the 12.95 mm listing |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **40 mm** (listing) = outer bezel silhouette at 9 o'clock, 37.55 px/mm. Check: gap between the lug inner edges 19.84 mm against 20 mm listed |
| Origin | Hand pivot (830, 1344); the 11 free index centres sit 0.96° counter-clockwise (std 0.06°): the photo is turned, the model is straight and the maps are sampled through the turn |
| Bezel | Smooth skirt 40.0 mm, 90 rounded teeth (tips 39.8, notches 38.6 mm), polished flat to the black insert (37.3 mm), insert 30.1 → 36.8 mm photo-mapped |
| Dial | Flat to the crystal ring (29.6 mm) with the orange minute track printed, 10.44 → 14.33 mm applied indices on top |
| Indices | Traced: lume mask per hour turned to 12, mean per type (trapezoid at 12, 6, 9 also used at 3 where the seconds hand crosses; bars), polished frame = lume + 5 px |
| Hands | Sword hour (8.3 mm) and minute (13.4 mm) with polished frames, lume and black tails; black seconds hand with an orange arrow, lume and a rectangular tail (rotated strips) |
| Lugs | Mean outline of the four lugs, traced down the case flank to 9 mm from the pivot (spread 0.16 mm), tips at 24.26 mm (photo 24.0 / 24.6: its 6 o'clock half is a little longer), brushed top sloping to the tip, polished edges; brushed 40 mm case ring under the bezel teeth |
| Crown | Screw-down, 6.5 mm across, 20.1 → 23.3 mm on the 3 o'clock axis, between brushed crown guards traced from the silhouette |
| Strap | Orange rubber from the photo, 19.4 mm, straight in the photo: each side sampled with the lug tips aligned, house 7 mm curl; buckle left out |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_scuba_pioneer_trace h82395331   # -> config/watches/hamilton-h82395331-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h82395331    # -> outputs/watches/hamilton-h82395331/dial.jpg, strap.jpg (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h82395331.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: 90 rounded bezel teeth over a dark skirt, traced lugs and crown guards, applied indices, sword hands, orange rubber strap with the 7 mm curl. GLB 2.28 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h82395331.glb` |
