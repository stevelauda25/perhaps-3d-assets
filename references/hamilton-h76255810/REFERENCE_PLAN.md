# Reference plan: Hamilton Khaki Aviation Pilot Pioneer Auto H76255810 (eggshell dial, moss green bezel, green leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method:
modelled brushed case and lugs, polished coin-edge bezel and onion crown, modelled hands; photo maps only for the dial print
with the green insert, and for the leather strap. File name `hamilton-h76255810`. Build code shared with H82395331
(`pipeline/steps/watch_hamilton_scuba_pioneer.py`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1209 × 1982 | `front_1209x1982.jpg` | HAVE, primary for everything (supplied by Irsyad). Under the 2000 px target |
| 2 | 3/4 from the crown side | none | GAP: heights are the house values scaled to the 11.4 mm listing |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **38 mm** (listing) = outer bezel silhouette at 9 o'clock, 26.21 px/mm. Check: gap between the lug inner edges 18.20 mm against 18 mm listed |
| Origin | Hand pivot (553, 967); the 12 lume plots of the railroad track sit 0.28° counter-clockwise: the photo is turned, the model is straight and the maps are sampled through the turn |
| Bezel | 120 fine teeth (tips 37.9, notches 37.3 mm) over a dark skirt, polished flat to the green insert (35.6 mm), insert 31.4 → 35.6 mm photo-mapped |
| Dial | Flat to the crystal ring (30.2 mm); numerals, logo and railroad track printed |
| Hands | Black (photo: black frames, light edge highlights): leaf hour hand (10.6 mm) with lume stem, lume leaf and a black spine; baton minute hand (15.0 mm) with three lume panels and a needle tip; needle seconds hand (14.7 mm) with a lozenge counterweight |
| Lugs | Mean outline of the four lugs, traced down the case flank to about 10 o'clock (spread 0.21 mm), tips at 22.66 mm (photo 22.3 / 23.0), brushed top sloping to the tip, polished edges |
| Crown | Onion crown on the 3 o'clock axis, 16 flutes: neck at the bezel, cone out to 7.1 mm across, barrel, rounded end at 22.8 mm (photo profile) |
| Strap | Green leather from the photo, 17.7 mm, straight in the photo with its keepers: each side sampled with the lug tips aligned, house 7 mm curl; buckle left out |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_scuba_pioneer_trace h76255810   # -> config/watches/hamilton-h76255810-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h76255810    # -> outputs/watches/hamilton-h76255810/dial.jpg, strap.jpg (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h76255810.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: 120 fine bezel teeth, traced lugs and case flank, onion crown, black leaf / baton / needle hands with lume, green leather strap with the 7 mm curl. GLB 2.10 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h76255810.glb` |
