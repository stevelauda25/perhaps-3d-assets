# Reference plan: Orient Star RE-AU0107E (green power reserve dial, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/orient-re-au0107e.glb`, built like `seiko-sur419p1.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, indices, numerals, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1194 × 2016 (2× working copy 2388 × 4032) | `front_1194x2016.jpg`, `front_2x_2388x4032.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 12.2 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 38.5 mm (48.55 px/mm on the 2× copy) |
| --- | --- | --- |
| Case diameter | **38.5 mm** (anchor, listing) | circle on the case flanks, centred 0.2 mm from the hand pivot (1123, 2008) |
| Lug width | 20 mm | end link 19.98 mm |
| Lug to lug | 46.9 mm | 45.25 mm (tips 22.1 mm top, 23.1 mm bottom) |
| Crystal ring, dial edge | not listed | 34.2 mm, 31.2 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, wide polished sloped bezel down to the flank | #1 |
| Lugs | Broad straight-sided lugs leaving the case at about 8.5 mm; brushed top, polished outer chamfer | #1 silhouette |
| Dial | Green sunburst centre, ribbed ring, minute track with ticks, printed lume dots | dial map |
| Power reserve | Silver arc 50-25-0 with a small black hand under 12 | dial map |
| Indices | Applied polished faceted batons 1.07 mm wide (11.2 to 14.4 mm); wide batons at 3 (outside the date, two dark grooves) and 9 (one groove) | #1 |
| Numerals | Applied polished serif XII and VI | #1, rebuilt from measured strokes |
| Date, logo | White date window with black frame at 3; Orient Star emblem, ORIENT STAR, AUTOMATIC | dial map |
| Hands | Polished faceted swords with pointed counter-tails and a polished collar; seconds needle with a dark counterweight | #1 |
| Crown | Fluted crown with an end cap at 3 | #1 |
| Bracelet | Five pieces per row: brushed outer links, narrow polished links, brushed centre link; centre joints 1.6 mm nearer the case; pitch 5.8 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 38.5 mm case (listing): the end link then measures the listed 20 mm |
| Heights | Front-relief reading of the listed 12.2 mm (no side photo) |
| Hand pose | The pose in #1 so the comparison render lines up |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_re_au0107e_trace   # -> config/watches/orient-re-au0107e-trace.json
python3 -B -m pipeline.orient_re_au0107e_dial    # -> outputs/watches/orient-re-au0107e/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
