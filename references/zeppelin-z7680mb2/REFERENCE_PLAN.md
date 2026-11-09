# Reference plan: Zeppelin 100 Jahre Chronograph Z7680MB2 (steel, black dial, three-column steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 committed 2026-11-09 (`models/watches/zeppelin-z7680mb2.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2700 × 4292 | `front_2700x4292.jpg` | HAVE, primary for everything |
| 2 | Back, 3/4, side | none | GAP: heights fitted to the listed 13 mm |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: bracelet 21.12 mm next to the lugs; lug to lug 48 mm traced (bottom lugs look longer: camera slightly off-axis) |
| Bracelet | Three-column steel links from the photo, not the listing's mesh (Irsyad 2026-11-09); house 7 mm curl from the lug tips |
| Origin | Hand pivot (1220, 2141); the case circle centre sits 11 px right and 15 px lower, the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z7680mb2.glb` |
| Print, telemeter and tachymeter scales, sub-dials, lume dots, date, airship logo | Kept in the dial map (flat); hands and hubs removed by a normalised blur fill |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, brushed band (20.1-21 mm) carrying the crown and pushers, polished sloped bezel (19.35-20.1 mm), black telemeter ring under the crystal |
| Lugs | Brushed blocks outside the bracelet, leave the case at 15.75 mm, tips 24.0 mm (mean) |
| Dial | Black sunray, tachymeter flange, three sub-dials (30-min counter at 9, seconds at 3, alarm at 6), date at 4:30, printed lume dots, airship logo |
| Hands | Steel lollipop hour and minute hands with a lume leaf and a lume disc; white chronograph needle with a long tail; white sub-dial hands (lozenge at 9) |
| Crown | Fluted, domed end, at 3 |
| Pushers | Two plain pushers at 2 and 4 |
| Bracelet | Three columns: brushed outer links, brushed centre links with polished sides; end link across all columns |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z7680mb2_trace   # -> config/watches/zeppelin-z7680mb2-trace.json
python3 -B -m pipeline.zeppelin_z7680mb2_dial    # -> outputs/watches/zeppelin-z7680mb2/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 52.0946 px/mm from the 42 mm case circle (fit on both flanks) |
| Rings | bezel inner 19.35, telemeter ring 18.2-19.35, dial edge 17.08 mm |
| Bracelet | 21.12 mm wide; centre column 0.39 of the half width (polished sides from 0.28); pitch 5.16 mm; first centre joint 25.93 mm |
| Crown | 90°, radius 2.78 mm, reaches 26.5 mm; pushers at 62.3° and 118.6°, head radius 1.44 mm, reach 24.7 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z7680mb2.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: brushed case band with a polished sloped bezel, photo dial, steel lollipop hands with lume, white chronograph and sub-dial hands, crown and two pushers, brushed lugs, three-column bracelet with the 7 mm curl |
