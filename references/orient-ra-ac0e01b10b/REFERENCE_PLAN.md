# Reference plan: Orient RA-AC0E01B10B (Contemporary, black dial, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied an angled photo only; the straight-on front is Orient USA's own product image of the same reference.

## Target asset

A front-facing GLB in `models/watches/orient-ra-ac0e01b10b.glb`, built like `orient-re-au0108g.glb` (wide polished bezel, faceted batons): front relief, flat back, 2.5D depth, modelled case, bezel, batons, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, Orient USA, 1600 × 1067 (2× working copy on white 3200 × 2134) | `front_orientusa_1600x1067.png`, `front_2x_white_3200x2134.png` | HAVE, primary for plan sizes and the dial map; shot a little from below |
| 2 | 3/4 from the crown side | `angled_1000x1531.jpg` | HAVE (Irsyad), case and bezel shape |
| 3 | Side from 3 o'clock | `side_orientusa_1600x1067.png` | HAVE, heights read by eye |

## Scale anchors

| Dimension | Listed | Measured at 40 mm (32.29 px/mm on the 2× copy) |
| --- | --- | --- |
| Case diameter | **40 mm** (anchor, listing) | case flanks |
| Lug width | 20 mm (sibling B10A) | end link 19.6 mm; bracelet 19.9 mm past the lugs |
| Lug to lug | **46.1 mm** (AC0E family, used) | 44.5 mm: 20.9 at 12 (leans away) and 23.6 at 6 |
| Bezel | not listed | polished, from the crystal ring at 18.4 mm to the case edge |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, bezel | Thin round case, wide sloped polished bezel | #1, #2, #3 |
| Dial | Black, printed minute track at the edge | dial map |
| Indices | Applied polished batons with a ridge at every hour; the 3 shortened beside the date; thin polished date frame | #1 |
| Hands | Faceted polished sticks (hour, minute); polished seconds needle with a paddle counterweight | #1 |
| Crown | Fluted crown with a smooth end cap | #1, #3 |
| Lugs | Brushed top with a polished outer facet | #1, #2 |
| Bracelet | Three columns, brushed; centre joints 1.75 mm nearer the case; pitch 6.55 mm (6 o'clock side) | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Orient USA image (same reference, the supplied photo is angled) |
| Scale | 40 mm case (listing); lug tips at 23.05 mm from the listed 46.1 mm lug to lug |
| Lug outline | 6 o'clock side of the silhouette (faces the camera), mirrored |
| Hand pose | The pose in #1 (about 10:08:43) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0e01b10b_trace   # -> config/watches/orient-ra-ac0e01b10b-trace.json
python3 -B -m pipeline.orient_ra_ac0e01b10b_dial    # -> outputs/watches/orient-ra-ac0e01b10b/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
