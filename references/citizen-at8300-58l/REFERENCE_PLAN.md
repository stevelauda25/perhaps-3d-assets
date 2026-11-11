# Reference plan: Citizen AT8300-58L (Promaster Navihawk A-T, 41 mm, blue dial, slide rule, steel bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-11; the official render is sharper and is the working reference.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1366 × 2048 | `front_official_1366x2048.png` | HAVE (Citizen official), primary for everything |
| 2 | Side from 3 o'clock | `side_official_1535x2048.png` | HAVE (Citizen official): crown, pushers, heights |
| 3 | Back | `back_official_1656x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | Front photo, 1223 × 2048 | `front_1223x2048.jpg` | HAVE (Irsyad): cross-check |

## Scale anchors

| Dimension | Listed | Measured at 41 mm (28.66 px/mm) |
| --- | --- | --- |
| Case width | **41 mm** (anchor, Citizen) | bezel radius about the dial centre on the alpha |
| Thickness | 11.87 mm | heights scaled to it |
| Bracelet | 21 mm (retailers) | 21.0 mm at the case |
| Horn to horn | 46 mm (retailer) | 45.4 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Brushed round case with broad horns; the end link sits in a recess between them | #1 alpha rows |
| Flanks | Crown guard block on the right with pushers at 2 and 4 and a knurled crown at 3; a shoulder and a knurled crown at 8 (slide rule) | #1, #2 |
| Bezel | Fixed steel ring, satin top, polished chamfers | #1 radial profiles |
| Dial | Blue sunray dial, grey city ring, inner and outer slide rules under the crystal, subdials at 12, 9 and 6, date at 3 | dial map |
| Indices | Applied polished batons with lume; small squares (a pair at 12, 3, 6, 9) | #1 white mask |
| Hands | Lozenge hour and minute hands, polished outline and lume (traced); white chronograph needle with a black hooked counterweight; black hub | #1 white mask, crops |
| Bracelet | Three columns, wide centre links starting half a link nearer the case | #1 joints at the bottom end |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | The official render (straight-on, transparent, 28.7 px/mm) |
| Scale | 41 mm case = the bezel (Citizen) |
| Origin | The dial centre (subdial hubs); the hand stack shows 0.2 mm off it and is placed on it |
| Subdial needles | Kept in the dial map |
| Bracelet curve | House curl: 7 mm radius from the end link tips |

## Phase 1 outputs

```sh
python3 -B -m pipeline.citizen_at8300_trace   # -> config/watches/citizen-at8300-58l-trace.json
python3 -B -m pipeline.citizen_at8300_dial    # -> outputs/watches/citizen-at8300-58l/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
