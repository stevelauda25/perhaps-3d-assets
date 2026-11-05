# Reference plan: Seiko 5 Automatic SNK361K1 (black dial, five-row steel bracelet)

Written 2026-11-05 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-05.

## Target asset

A front-facing GLB in `models/watches/seiko-snk361k1.glb`, built like `seiko-snk607k1.glb`: front relief, flat back, 2.5D depth, case/bezel/indices/hands/bracelet as geometry, dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3170 × 6256 | `front_3170x6256.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights reuse the SNK607K1 values |
| 3 | Back | none | not needed for the flat-backed front asset |

#1 is straight-on and sharp. The polished bezel and case show bright reflection arcs: lighting, not shape.

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **36 mm** | Irsyad, 2026-11-05 |
| Bracelet width next to the case | not listed | measured 18.2 mm (22–24 mm from the pivot) at the 36 mm case |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, wide sloped polished bezel; a full circle, the end links run under it at 12 and 6 | #1, Irsyad |
| Lugs | Broad lugs that flare from the case flank, tips at 20.0 mm (lug to lug 40.0 mm) | #1 silhouette |
| Crystal | Flat, inside a dark gasket ring at 14.1–14.5 mm | #1 |
| Dial | Plain black; edge at 13.6 mm, thin polished rehaut ring | #1 |
| Minute track | White ticks around the outer edge | #1, dial map |
| Hour indices | Applied batons, polished outline with a black centre and a white lume block at the outer end; 9.4–12.8 mm; double at 12; lume block only at 3 (day-date) | #1 |
| Logo, print | `SEIKO`, `5` shield, `AUTOMATIC 21 JEWELS`, small print at 6: in the dial map. The seconds hand crosses `SEIKO` and the shield in #1, so that block comes from the SNK381K1 front photo (same applied logo, no hand over it) | #1, SNK381K1 #1 |
| Day-date | `MON 7`, polished frame 7.5 × 2.6 mm, centre 8.3 mm right of the pivot | #1 |
| Hands | Polished rim around a black centre (skeleton), rounded tips and tail ends, white lume inserts on hour and minute; seconds hand a thin polished needle with a long paddle tail; polished hub with a black ring and polished cap | #1, Irsyad |
| Crown | Small knurled crown at 4 o'clock | #1 |
| Bracelet | Five columns: brushed outer and centre links in step, polished mid links half a row offset; rows 5.42 mm apart; tapers from 18.5 mm to 14.6 mm | #1 |
| End link | Solid, five columns, between the lugs (17.4 mm wide) from the case to the lug tips | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | 36 mm (Irsyad, 2026-11-05; v001–v002 were built at 37 mm from listings) |
| Bracelet layout | Follows the photo, not the SNK607K1 layout (Irsyad, 2026-11-05: each watch keeps its own construction): a solid five-part end link from the case to the lug tips, then centre and outer links in step and mid links half a row offset |
| Hand pose | The pose in #1 so the comparison render lines up |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snk361_trace   # -> config/watches/seiko-snk361k1-trace.json
python3 -B -m pipeline.seiko_snk361_dial    # -> outputs/watches/seiko-snk361k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 77.68 px/mm from the 36 mm case flanks; origin = hand pivot (1563, 3136) |
| Crystal ring, dial edge | 14.43 mm, 13.65 mm |
| Indices | 9.41–12.84 mm, lume block from 12.00 mm; width 0.80 mm (12: 1.98 mm) |
| Hands (10:07:47) | hour 304.6°, 7.83 mm; minute 39.5°, 11.71 mm; seconds 350.8°, 11.82 mm, tail 4.64 mm |

Hands, day-date, logo boxes, crown and bracelet columns are read from gridded crops (`MANUAL_PX`, ±8 px ≈ ±0.1 mm); ring and index radii come from radial profiles. The dial map fills the hand zones by inpainting (plain black dial) and replaces the `SEIKO` + shield block with the same logo from the SNK381K1 photo.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snk361k1-v005.json   # build, GLB, white comparison render
```

| Version | Change | Board |
| --- | --- | --- |
| v001 | First front relief; heights, 2.5D depth, glass, steel textures and bracelet bend (23 mm radius from the lug tips) as SNK607K1 v009 | `outputs/jobs/seiko-snk361k1-v001/board_front.png` |
| v002 | Lugs start where the silhouette leaves the 37 mm case circle (9.5 mm, was 10.5 mm from SNK607K1); 1.6 MB GLB | `outputs/jobs/seiko-snk361k1-v002/board_front.png`, `board_measured.png` |
| v003 | 36 mm case (Irsyad) instead of 37 mm: every plan size 2.7 % smaller, heights unchanged; lugs from 9.25 mm, bend from the lug tips at 20.0 mm; 1.6 MB GLB | `outputs/jobs/seiko-snk361k1-v003/board_front.png`, `board_measured.png` |
| v004 | Case a full circle at 12 and 6 (Irsyad): no flat where the end link meets it | `outputs/jobs/seiko-snk361k1-v004/board_front.png` |
| v005 | Rounded hand tips and tail ends (Irsyad); hands as a polished rim around a black centre; clean `SEIKO` + 5 shield in the dial map from the SNK381K1 photo (template match 0.93) | `outputs/jobs/seiko-snk361k1-v005/board_front.png` |

## Known gaps

- Only a front photo: case height, lug drop and crown length are the SNK607K1 values.
- 36 mm is the owner's value; no listed bracelet width to cross-check it.
- Mid bracelet links are built polished from their highlights in #1; confirm with the designer.
