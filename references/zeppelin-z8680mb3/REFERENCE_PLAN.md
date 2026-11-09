# Reference plan: Zeppelin 100 Jahre Chronograph Z8680MB3 (steel, cream dial, three-column steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 2 committed 2026-11-10 (`models/watches/zeppelin-z8680mb3.glb`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2636 × 4096 | `front_2636x4096.png` | HAVE, primary for everything |
| 2 | Back, 3/4, side | none | GAP: heights kept from Z7680MB2 (same case) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing). Check: bracelet 21.22 mm next to the lugs; lug to lug 47.75 mm traced |
| Construction | Same case and bracelet as Z7680MB2; build step, trace and dial scripts copied from it with this photo's values |
| Bracelet | Three-column steel links from the photo, not the listing's mesh (as Z7680MB2, Irsyad 2026-11-09); house 7 mm curl from the lug tips |
| Origin | Hand pivot (1247, 2032); the case circle centre sits 4 px right and 10 px lower, the model keeps the case on the pivot |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z8680mb3.glb` |
| Print, telemeter and tachymeter scales, sub-dials, lume dots, date, airship logo | Kept in the dial map (flat); hands and hubs removed by a normalised blur fill |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, brushed band (19.7-21 mm) carrying the crown and pushers, polished sloped bezel (18.58-19.7 mm), cream telemeter ring under the crystal |
| Lugs | Brushed blocks outside the bracelet, leave the case at 15.0 mm, tips 23.9 mm (mean) |
| Dial | Cream, tachymeter flange, three sub-dials (30-min counter at 9, seconds at 3, alarm at 6), date at 4:30, printed dots, airship logo |
| Hands | Black hour and minute hands with a leaf and an open ring; black chronograph needle with a long tail; black sub-dial hands (lozenge at 9, two arrow-tailed alarm hands at 6) |
| Crown | Fluted, domed end, at 3 |
| Pushers | Two plain pushers at 2 and 4 |
| Bracelet | Three columns: brushed outer links, brushed centre links with polished sides; end link across all columns |

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z8680mb3_trace   # -> config/watches/zeppelin-z8680mb3-trace.json
python3 -B -m pipeline.zeppelin_z8680mb3_dial    # -> outputs/watches/zeppelin-z8680mb3/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 49.3001 px/mm from the 42 mm case circle (fit on both flanks) |
| Rings | bezel inner 18.58 mm |
| Bracelet | 21.22 mm wide; centre column 0.38 of the half width (polished sides from 0.27); pitch 4.95 mm; first centre joint 26.41 mm |
| Crown | 88.8°, radius 2.6 mm, reaches 25.2 mm; pushers at 60.4° and 119.6°, head radius 1.46 mm, reach 24.0 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z8680mb3.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief from the Z7680MB2 construction: cream photo dial, black hands with open rings, black sub-dial hands, crown and two pushers, brushed lugs, three-column bracelet with the 7 mm curl |
| 2 | 2026-11-10 | More detail: hour, minute and sub-dial hands traced from the photo (black on cream, threshold inside each hand's zone), ring centres from the bright hole, alarm hands and the bar from the hub traced as one group, polished ring on the main hub, polished pins on the sub-dial hubs; dial fill follows the traced shapes |
