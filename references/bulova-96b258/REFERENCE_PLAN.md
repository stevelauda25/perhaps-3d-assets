# Reference plan: Bulova 96B258 (Lunar Pilot chronograph, 45 mm, steel bracelet)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Bulova's official render.

## Target asset

A front-facing GLB in `models/watches/bulova-96b258.glb`: front relief, flat back, 2.5D depth, modelled case, pusher shoulders, bezel, indices, hands, crown and bracelet; the dial (with chapter ring and tachymeter) from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1243 × 2048 | `front_official_1243x2048.png` | HAVE (Bulova official), primary for everything |
| 2 | Side from 9 o'clock | `side_official_1657x2048.png` | HAVE (Bulova official): heights |
| 3 | Back | `back_official_1249x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | 3/4 from the left | `angled_2332x3815.jpg` | HAVE (Irsyad): pushers, bezel, bracelet |

## Scale anchors

| Dimension | Official | Measured at 45 mm (22.91 px/mm) |
| --- | --- | --- |
| Case width | **45 mm** (anchor) | twice the widest case half width (left flank), hand pivot (594, 997) |
| Lug width | 20 mm | bracelet 19.8 mm |
| Lug to lug | not listed | 52.2 mm in the render |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Brushed, integrated horns, the bracelet's end link in a recess between them | #1, alpha outline |
| Pushers | Shoulders at 2 and 4 (rectangular pushers in #4) | #1, right silhouette beyond the case |
| Bezel | Polished, sloping up to the crystal, 19.6 to 20.8 mm radius | #1 |
| Dial | Black; sloped chapter ring with 1/5 s ticks; black tachymeter flange; subdials at 9, 3 and 6 with concentric grooves; date at 4:30 | dial map |
| Indices | Applied polished frames with white lume: batons, a wide 12, squares at 3, 6 and 9 | #1, radial profiles |
| Hands | Lume hour and minute hands in a polished frame; white chronograph hand with counterweight and lozenge; white subdial needles | #1, straightened strips |
| Crown | Fluted, at 3 | #1 |
| Bracelet | Three brushed columns, centre joints offset from the outer ones | #1, link joints on both ends |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Bulova's official render (the supplied photo is angled) |
| Scale | 45 mm case width (official) |
| Case centre | The render's silhouette sits 3 px right of the hand pivot; the case is built symmetric about the pivot |
| Subdial needles | Kept in the dial map under the modelled needles, so the numerals they cross stay whole |
| Dial print | White print redrawn at 4x the render's resolution (crisp edges in the dial close-up) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_96b258_trace   # -> config/watches/bulova-96b258-trace.json
python3 -B -m pipeline.bulova_96b258_dial    # -> outputs/watches/bulova-96b258/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build. Approved |
