# Reference plan: Hamilton Jazzmaster Viewmatic Auto H32515135 (black waffle dial, applied indices, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method:
modelled case, bezel, crown, applied indices and numerals, hands and bracelet; the photo map only for the dial print. File
name `hamilton-h32515135`. Build code shared with H64455523 (`pipeline/steps/watch_hamilton_scuba_pioneer.py`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE, Hamilton's official render, primary for everything |
| 2 | 3/4 from the crown side | `three_quarter_1000x1666.jpg` | HAVE (retailer photo): case and bracelet heights by eye |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **40 mm** (listing) = case silhouette at 9 o'clock on the pivot row, 23.3 px/mm. Check: bracelet between the lugs 20.258 mm against 20 mm |
| Origin | Hand pivot (998, 965). The dial print is turned 1.3° counter-clockwise in the render (minute track phase); case and bracelet are straight. Hands, indices and numerals are turned back into the straight model |
| Case | One polished body from the render's alpha outline (case, lugs and the wider crown-side flank), 12 and 6 o'clock halves averaged, lug tips 25.343 mm |
| Bezel | Smooth polished, two steps: 38.7 → 36.5 → 35.0 mm, black rehaut ring to the 34.2 mm dial |
| Indices | Applied polished kites traced (mean of the eight bar hours), numerals 12, 9, 6 traced with their holes |
| Hands | Polished leaf-sword hour (9.5 mm) and minute (15.7 mm) with lume, polished seconds needle with a short counterweight |
| Bracelet | Five columns (edges 2.12 / 6.37 / 10.13 mm): polished outer and centre links (joints 24.3 mm, 7 mm pitch), brushed middle links half a row nearer the case; house 7 mm curl from the first outer joint |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_jazz_king_trace h32515135      # -> config/watches/hamilton-h32515135-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h32515135   # -> outputs/watches/hamilton-h32515135/dial.jpg (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h32515135.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: polished body from the render outline, two-step bezel, applied kites and numerals 12/9/6, leaf-sword hands, five-column bracelet with the 7 mm curl. GLB 1.63 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h32515135.glb` |
