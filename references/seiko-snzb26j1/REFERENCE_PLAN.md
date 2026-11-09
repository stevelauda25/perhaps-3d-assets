# Reference plan: Seiko 5 Sports SNZB26J1 (gold tone, gold dial, gold bezel, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Build structure follows the [SNZ450J1](../seiko-snz450j1/REFERENCE_PLAN.md).

## Target asset

A front-facing GLB in `models/watches/seiko-snzb26j1.glb`: front relief, flat back, 2.5D depth; case, bezel and its print, indices, hands, day-date frame, crown and bracelet as geometry; dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2048 × 2048 (watch about 1050 px wide) | `front_psb_2048.jpg` | HAVE, primary for everything |
| 1t | Front, target look: bezel pip at 12, MON 15, 10:09, 1000 × 1672 | `front_target_1000x1672.png` | HAVE (Irsyad): bezel position, day-date, time, colours. Shapes stay from #1 |
| 1b | Front, turned slightly | `front_jomashop_1200.jpg`, `front_timepiece_900.jpg` | cross-check only (bezel turned differently) |
| 2 | 3/4 from the crown side | `three_quarter_crown_jomashop_1200.jpg` | HAVE: crown, bezel height, bracelet profile |
| 3 | Back | `back_jomashop_1200.jpg` | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **40 mm** across the knurled bezel skirt | spec sheet; listings say 39-42 mm. Irsyad took the recommendation (2026-11-09) |
| Bracelet next to the case | 21.3 mm measured | no lug width listed |

## Parts seen

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, hidden under the bezel except four polished lugs and the crown guard | #1 |
| Bezel | Wide flat polished gold ring (15.3-19.5 mm) with engraved black numerals 5-55, a knurled skirt under it, four raised square pads at 0/15/30/45 carrying black triangles and a lume pip in a black square at 0. Photographed with the pip at 149 deg | #1 |
| Crown | Fluted gold crown at 3 | #1, #2 |
| Dial | Gold sunburst with a fine pattern, printed minute track, `SPORTS`, `WATER 100M RESIST`, `AUTOMATIC`, `23 JEWELS`, small print at 6 | #1, map |
| Indices | Cream lume in gold frames; 6 and 9 wider; double baton with a pointed end at 12; none at 3 | #1 |
| Logo | Applied `SEIKO` and 5 shield (fitted from the SNZ450J1 trace) | #1 |
| Day-date | White window `SUN 10`, gold frame | #1 |
| Hands | Gold sword hour and minute hands with two lume windows split by a black bar; needle seconds with a lume disc on its tail | #1 |
| Bracelet | Three columns, brushed; centre about half the width; centre joints 0.84 of a row past the outer ones (shallow chevron ends, modelled square); rows 6.5 mm | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snzb26_trace   # -> config/watches/seiko-snzb26j1-trace.json
python3 -B -m pipeline.seiko_snzb26_dial    # -> outputs/watches/seiko-snzb26j1/dial_photo.jpg (regenerated, not committed)
```

Scale 26.3 px/mm; origin = middle of the crystal ring (983, 1044); hands read 10:08:33.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snzb26j1.json --force   # step watch_seiko_snzb24 with the SNZB24J1 trace; build, GLB, white comparison render (overwrites outputs/jobs/seiko-snzb26j1/)
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: round case cut back between the lugs, wide gold bezel with knurled skirt, four raised pads and traced black print, cream-lume batons, sword hands, three-column bracelet with the 7 mm house curl; 4.3 MB GLB, waiting for review |
| 2 | 2026-11-09 | Matched to the target photo `front_target_1000x1672.png` (Irsyad): bezel turned so the pip sits at 12, day-date redrawn MON 15, hands at 10:09 (seconds needle under the hour hand), gold hand bars, pale gold index lume, yellower gold, brighter dial map; print letters hidden by the old seconds hand patched from the target photo; clean triangles and a centred pip; case rebuilt as lug plates with straight inner edges; longer crown; 4.0 MB GLB, waiting for review |
| 3 | 2026-11-09 | Gold version of SNZB24J1 (Irsyad: same watch, only gold): built by `watch_seiko_snzb24` from the SNZB24J1 trace (same case and dial layout); all metal gold, satin bezel top with polished pads, brushed links with polished stripes; SNZB26J1 dial map (MON 15) and target time 10:09:49; 4.5 MB GLB, committed to `models/watches/seiko-snzb26j1.glb` |

## Known gaps

- Heights are estimated (listed 12 mm thick), not measured.
- The knurled skirt is drawn with 120 teeth, not counted.
- The dial map keeps faint streaks inside the hour and minute hand zones; the hands cover them.
- The target photo shows no seconds needle (likely retouched): the needle lies under the hour hand and its tip shows past it.
