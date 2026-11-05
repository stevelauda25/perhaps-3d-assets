# Reference plan: Seiko 5 Automatic SNK607K1 (black textured dial, steel bracelet)

Written 2026-11-05 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Reference set approved by Irsyad on 2026-11-05; the built asset still needs designer approval.

## Target asset

A front-facing GLB in `models/watches/seiko-snk607k1.glb`, matching the existing Casio GLBs in that folder: modelled from the front, flat back, case/bezel/indices/hands/bracelet as geometry, dial print and texture from a map. Tracker task: Catalog 1, `SNK607K1`, assigned to Irsyad.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3224 × 6212 | `front_3224x6212.png` | HAVE, primary for planform, dial, hands |
| 2 | Back, bracelet closed in a loop, clasp, white background, 3200 × 2290 | `back_loop_clasp_3200x2290.png` | HAVE (not needed for the flat-backed front asset) |
| 3 | 3/4 from the crown side, white background, 2374 × 3200 | `three_quarter_crown_side_2374x3200.png` | HAVE, for heights, crown, lug side, case flank |
| 4 | Macros: crown, dial, indices, bracelet link | none (crops of #1 and #3) | PARTIAL |
| 5 | Side profile and lug-end view, orthographic | none | MISSING; #3 is the substitute |

Quality and artefacts:

- #1 is straight-on: the bezel band is 213 px on the left and 207 px on the right; the crystal ring is 2240 × 2273 px (height/width 1.015). Trace the planform from it without correction.
- #1 is sharp enough for indices, hands, logo, day-date and bracelet links. `AUTOMATIC 21 JEWELS` and the small print at 6 are broken up by the dial texture; #3 shows the same print more clearly.
- The hands cover parts of the dial texture and print in #1; the dial map cannot be cut straight from the photo.
- Highlights on the dial bumps and the polished bezel are lighting, not print or shape.
- #3 shows a different date (`THU 1`) and hand pose; use it for shapes only.

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **37 mm** | chosen by Irsyad on 2026-11-05; listings say 36, 37 or 38 mm |
| Case thickness | 11 mm (most listings) | consistent, not verified by Seiko |
| Bracelet width at the case | 20 mm (World of Watches, eBay); 18 mm lug width at PSB Watches | second anchor, consistent with #1 (below) |
| Lug-to-lug | not listed | measure in #1 |

Measured in #1 (pixels):

| Feature | Pixels | At 37 mm case (71.9 px/mm) |
| --- | --- | --- |
| Case outer width at the dial centre row (x 301–2962) | 2661 | 37 mm (anchor) |
| Dark crystal ring (x 514–2754, y 1967–4241) | 2240 × 2273 | ≈ 31.2 mm |
| Crystal ring centre | x ≈ 1634, y ≈ 3104 | |
| Hand hub (red cap) | x ≈ 1618, y ≈ 3102 | |
| Bracelet, first row above the case (x ≈ 865–2330, side shading to 2400) | 1465–1535 | ≈ 20.4–21.3 mm |
| Centre link, same row (x 1270–1985) | 715 | ≈ 9.9 mm |
| Crown (knurled part) | x ≈ 2876–2973, y ≈ 3490–3890 | |

A 37 mm case and a 20 mm bracelet agree within 2–6 % in #1, so the two anchors are consistent.

## Part by part

| Part | True shape | Source | Open question |
| --- | --- | --- | --- |
| Case | Round, wide sloped polished bezel band; polished flank that bulges out around the crown; brushed tops on the shoulders and lugs | #1, #3 | exact flank curve (no orthographic side view) |
| Lugs | Squared-off lug ends, brushed top, polished sides, a drilled spring-bar hole on the side of each lug | #3 | lug drop: fit from #3 |
| Crystal | Flat Hardlex inside a dark gasket ring, sitting just below the bezel top | #1, #3 | crystal height: fit from #3 |
| Dial | Black with a diagonal-vertical woven texture: rows of raised oval bumps that catch light | #1, #3 | bump size and depth for a normal map |
| Minute track | Fine white ticks around the outer edge of the dial | #1, #3 | |
| Hour indices | Applied polished batons with a dark centre line at 1, 2, 4, 5, 7, 8, 9, 10, 11; double baton at 12; short baton at 6 | #1, #3 | baton height |
| Lume | White dots on the outer edge at each hour, including 12 and 6 | #1, #3 | |
| Logo | `SEIKO` applied, polished outline letters; `5` shield applied, polished | #1, #3 | |
| Print | `AUTOMATIC` / `21 JEWELS` white below the centre; small print either side of 6 | #3 is clearer | exact wording of the small print |
| Day-date | Window at 3: black discs, white day and date, polished frame | #1 (`THU 11`) | which day and date to show (use #1) |
| Hands | Polished hour and minute hands with white lume strips; thin dark red seconds hand with a short counterweight and a white tip; red hub cap | #1 | |
| Crown | Small straight-knurled crown at **4 o'clock**, about 8–9 flutes, partly sunk into the case flank | #1, #3 | crown length |
| Bracelet | Three-row steel bracelet: brushed tops, polished chamfers, centre link wider than the outer links; fitted end links shaped to the case | #1, #3 | |
| Back (not built) | Screw-down exhibition caseback showing the 7S26 rotor, `SEIKO`, `ST.STEEL`, `WATER RESISTANT`; fold-over clasp with Seiko 5 logo | #2 | |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | 37 mm (Irsyad, 2026-11-05) |
| Hand pose | Free choice; use the pose in #1 so the Phase 3 comparison lines up pixel for pixel |
| References | #1 for planform, #3 for heights; no orthographic side view, so lug drop, flank curve and crystal height are fitted from #3 and flagged as inferred |
| OpenCV for tracing | Installed: `opencv-python-headless` 5.0.0 (user site-packages) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_trace    # -> config/watches/seiko-snk607k1-trace.json
python3 -B -m pipeline.seiko_dial     # -> outputs/watches/seiko-snk607k1/dial_photo.png (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 72.32 px/mm from the 37 mm case outline; origin = hand pivot (1620, 3100) |
| Cross-check | bracelet next to the case 20.26 mm against 20 mm (1.3 %) |
| Crystal ring | radius 15.66 mm |
| Dial texture edge, minute track, lume dots | radius 13.3 mm; 12.5–13.1 mm; 12.19 mm |
| Indices | batons from 8.6 to 11.4 mm (6 o'clock: 8.7 to 10.6 mm) |
| Hands (10:07:19) | hour 302.3°, 7.77 mm; minute 40.7°, 11.67 mm; seconds 116.6°, 11.92 mm, tail 4.69 mm |
| Day-date frame | 7.47 × 2.45 mm, centre 8.37 mm right of the pivot |
| Logo | `SEIKO` 5.81 × 1.04 mm at 6.33 mm above the pivot; `5` shield centre 4.5 mm above |
| Crown | 2.31 × 3.94 mm box, centre at 112.9°, 18.96 mm from the pivot |
| Bracelet | tapers from 20.2 mm next to the case to about 17 mm; rows about 6 mm apart |

Indices, hands, logo, day-date and crown are read from gridded crops (`MANUAL_PX` in `pipeline/seiko_trace.py`, ±5 px ≈ ±0.07 mm) because the woven dial defeats threshold tracing. The hand pivot sits 0.35 mm left of the fitted case centre in the photo; the build treats them as concentric.

The dial map keeps the photo's lighting, indices, logo and print; the hands, their shadows and the crystal reflection are filled from the woven pattern. Faint fill seams remain within 1.3 mm of the pivot, under the 3D hands and hub.

## Build status (Phases 2–4, not approved)

```sh
blender -b --factory-startup --python pipeline/watch_empty_base.py -- assets/watches/baseline/empty_base.blend   # once per machine
python3 -B -m pipeline.jobs run jobs/seiko-snk607k1-v003.json                 # build, GLB, white comparison render
python3 -B -m pipeline.jobs run jobs/seiko-snk607k1-v003-presentation.json    # dark-kit previews (front, macro, crown side)
```

| Version | Change | Board |
| --- | --- | --- |
| v001 | First front relief | `outputs/jobs/seiko-snk607k1-v001/board_front.png` (its render folder now holds a v002 render) |
| v002 | Lugs follow the case outline; centre links start at the case, outer links at the lug tips | `outputs/jobs/seiko-snk607k1-v002/board_front.png` |
| v003 | Applied 5 shield (traced outline) and raised lume dots | `outputs/jobs/seiko-snk607k1-v003/board_front.png`, `outputs/jobs/seiko-snk607k1-v003-presentation/board_presentation.png` |

GLB: `outputs/jobs/seiko-snk607k1-v003/seiko-snk607k1.glb` (metres, dial facing +Z, dial map embedded). It goes to `models/watches/seiko-snk607k1.glb` only after designer approval. Measured: case 37.0 mm, bracelet next to the case 20.27 mm, lug to lug 43.5 mm. Materials are plain Principled BSDFs (not library presets) so the GLB keeps the dial texture.

## Known gaps

- No orthographic side or lug-end view: heights come from the 3/4 view.
- No verified Seiko specification: 37 mm is the owner's choice, not a measured value.
- Dial texture needs a clean map: rebuild it from a clean patch of the woven pattern instead of cutting it from the photo with the hands on top.
