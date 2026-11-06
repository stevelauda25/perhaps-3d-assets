# Reference plan: Seiko SUR419P1 (blue dial, quartz, three-column steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-06.

## Target asset

A front-facing GLB in `models/watches/seiko-sur419p1.glb`, built like `seiko-snk607k1.glb`: front relief, flat back, 2.5D depth, case/bezel/indices/hands/bracelet as geometry, dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3366 × 5871 | `front_3366x5871.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights reuse the SNK607K1 values, scaled to the 7.9 mm listed thickness |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 39.4 mm (72.08 px/mm) |
| --- | --- | --- |
| Case diameter | **39.4 mm** (anchor, Irsyad) | circle on the case flanks, centred on the hand pivot (1637, 2813) |
| Lug to lug | 46.4 mm | 45.4 mm (tips 22.1 mm top, 23.3 mm bottom: the photo is slightly larger toward 6) |
| Lug width | 20 mm | bracelet 19.1 mm just past the top lug tips, 18.7 mm past the bottom ones (tapers) |
| Bezel inner edge, dial edge | not listed | 34.0 mm, 32.0 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, wide polished sloped bezel, a step ring at about 18.6 mm, polished flank | #1 |
| Lugs | Long polished lugs flowing from the case flank, tips at about 22.7 mm | #1 silhouette |
| Crystal | Flat, inside the bezel at 17.0 mm | #1 |
| Dial | Blue sunburst; outer track with white minute dots and a castellated inner edge; centre guilloché disc with a castellated ring | #1, dial map |
| Hour indices | Applied polished faceted batons, 1.1 mm wide at the outer end, 0.5 mm at the inner end, at every hour but 3, 6 and 12; a short baton at 3 outside the date | #1 |
| Numerals | Applied polished `12` and `6` with clean outlines | #1: raised plates traced by threshold |
| Logo, print | `SEIKO` (white), `MOV'T JAPAN 6N52-00B8 R5 2` at 6 | dial map |
| Date | Black window at 3, `28` in white, no polished frame | dial map |
| Hands | Polished faceted pointed batons (hour, minute); thin polished seconds needle with a short tail; small hub | #1, measure in Phase 1 |
| Crown | Fluted crown with a collar at 3 o'clock | #1 |
| Bracelet | Three columns: wide centre link (half width 5.0 mm) with two lengthwise grooves at 3.4 mm, outer links; centre joints 1.2 mm nearer the case than the outer ones; pitch 6.35 mm. Centre polished, outer brushed (Irsyad, 2026-11-06) | #1 |
| End link | Between the lugs, from under the case to the lug tips, three columns; the first centre link reaches into it | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 39.4 mm case (Irsyad, 2026-11-06), although the photo gives lug to lug 46.0 mm and 19.3 mm bracelet past the lugs |
| Bracelet finish | Centre links polished, outer links brushed (Irsyad, 2026-11-06) |
| Heights | SNK607K1/SNK361K1 values scaled to the listed 7.9 mm (crystal top 7.75 mm before the depth scale) |
| Hand pose | The pose in #1 so the comparison render lines up |
| Bracelet curve | Much tighter than the house 23 mm (Irsyad, 2026-11-06): 7 mm radius from the lug tips to about 125°, so the ends roll back under the watch; links bend with the curve instead of turning as rigid pieces (the house rule for rigid links does not apply to this model); 31.0 mm from the pivot in the front view, 10.7 mm drop |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_sur419_trace   # -> config/watches/seiko-sur419p1-trace.json
python3 -B -m pipeline.seiko_sur419_dial    # -> outputs/watches/seiko-sur419p1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 72.21 px/mm from the 39.4 mm case flanks; origin = hand pivot (1636, 2812) |
| Crystal ring, dial edge | 16.97 mm, 16.04 mm |
| Lug tips | 22.4 mm (12), 23.6 mm (6), mean 23.0 mm |
| Indices | 11.0–14.9 mm; short one at 3: 13.1–15.0 mm |
| Hands (10:07:42) | hour 302.0°, 9.21 mm; minute 35.3°, 13.44 mm; seconds 145.9°, 14.05 mm, lancet tail 4.81 mm |

The dial map fills each hand zone (hand, dark facet and shadow) from the same radius 12°, 24° … away: 12° is a whole number of periods of the 150 guilloché rays, the 90 teeth on both castellated rings and the 60 minute dots. The rotation centre is the guilloché centre (3, 6 px from the pivot); the sunburst lighting comes from around each hand. Near the pivot the rays are copied from 2× and 3× further out.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-sur419p1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-sur419p1/)
```

One job and one output folder; each change overwrites them. Board: `outputs/jobs/seiko-sur419p1/board_front.png`.

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: house depth, glass, steel and bracelet bend (23 mm radius from the lug tips); 2.2 MB GLB |
| 2 | 2026-11-06 | Bracelet curls away like the official photos: 8 mm radius from 1 mm past the lug tips, bracelet to 36 mm along its length (Irsyad); 2.1 MB GLB |
| 3 | 2026-11-06 | More curl (Irsyad): 7 mm radius from the lug tips, about 125°, ends roll under the watch; 2.2 MB GLB |
| 4 | 2026-11-06 | Links bend with the curve (sliced every 0.4 mm) instead of turning as rigid pieces, so the curve is smooth like the Casio straps (Irsyad) |

## Known gaps and artefacts

- Only a front photo: case height, lug drop and crown length are not visible.
- A small dark patch remains in the dial map just right of the `SEIKO` plate, where the minute hand crossed its edge.
- The bracelet sits about 1 mm right of the pivot in the photo (watch slightly turned); the build centres it.
- Bright arcs on the bezel and case are reflections, not shape.
- Hands cross the guilloché centre: the dial map must rebuild the radial pattern under them.
