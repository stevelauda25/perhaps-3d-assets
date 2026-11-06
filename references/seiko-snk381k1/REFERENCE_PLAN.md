# Reference plan: Seiko 5 Automatic SNK381K1 (black dial, Arabic numerals, steel bracelet)

Written 2026-11-05 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Same SNK case family as the [SNK607K1](../seiko-snk607k1/REFERENCE_PLAN.md); heights are taken from that build.

## Target asset

A front-facing GLB in `models/watches/seiko-snk381k1.glb`, like `seiko-snk607k1.glb`: flat back, case, crystal, hands, day-date frame, 5 shield, crown, lugs and bracelet as geometry; numerals, logo letters and print from the dial map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 4698 × 9372 | `front_4698x9372.png` | HAVE, primary for everything |
| 2 | Back | none | MISSING (not needed for the front asset) |
| 3 | 3/4 view | none | MISSING; heights reuse the SNK607K1 3/4 fit |
| 4 | Macros | crops of #1 | PARTIAL |
| 5 | Side profile | none | MISSING |

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter | 37 mm | listings; same as the SNK607K1 |
| Bracelet next to the case | 19.1 mm measured against 20 mm in listings (4.5 % off) | consistent enough; the build asserts the measured 19.1 |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, lugs, crown | SNK case: wide sloped polished bezel, brushed lug tops, knurled crown at 4 o'clock (112.5°) | #1; heights from SNK607K1 |
| Crystal | Dark gasket ring at 15.09 mm radius (SNK607K1: 15.66) | #1 |
| Dial | Plain black; applied polished Arabic numerals with white fill, white minute dots, larger hour dots, no 3 (day-date) | #1, kept in the map |
| Logo | Applied `SEIKO` letters (map) and a polished `5` shield (traced, geometry) | #1 |
| Day-date | Window at 3, polished frame 7.79 × 2.75 mm, red `SUN`, white `12` | #1 |
| Hands | Leaf-shaped polished hour and minute hands with white lume; dark seconds hand with a lume disc (0.69 mm, rim 0.87 mm) on its 6.1 mm tail; black hub cap with a polished ring | #1 |
| Bracelet | Five columns: wide brushed outer links, narrow polished strip, mid links half a row off, narrow centre links; solid end link between the lugs; row pitch about 5.5 mm | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snk381_trace    # -> config/watches/seiko-snk381k1-trace.json
python3 -B -m pipeline.seiko_snk381_dial     # -> outputs/watches/seiko-snk381k1/dial_photo.jpg (regenerated, not committed)
python3 -B -m pipeline.jobs run jobs/seiko-snk381k1.json
```

Scale 111.73 px/mm, origin = hand pivot (2292, 4677). Hands read 10:08:50. The dial map is the photo with the hands and their shadows inpainted away; numerals beside a hand are kept out of the fill.

## Decisions to confirm with the owner

| Question | Current choice |
| --- | --- |
| Case diameter | 37 mm (listings), not yet confirmed by Irsyad |
| 3/4 and back photos | none supplied; heights copied from the SNK607K1 |

## Build status

| Version | Change | Board |
| --- | --- | --- |
| v001 | First front relief: numerals in the dial map, leaf hands, seconds tail disc, five-column bracelet, bend radius 28 mm | `outputs/jobs/seiko-snk381k1-v001/cmp-front.png` |
| v002 | House values from the SNK607K1 v009: bend from the lug tips (21.5 mm), radius 23 mm; dial map also removes hand shadows, sharpen 0.6, JPEG 93 (GLB 2.2 MB) | `outputs/jobs/seiko-snk381k1-v002/board_front.png` |
| v003 | Full 5 shield plate: the trace box was too narrow and cut off its right side, which then showed the flat photo in a different shade | `outputs/jobs/seiko-snk381k1-v003/board_front.png` |
| curl | Bracelet links bend with a smooth 7 mm curl from the lug tips, as on SUR419P1 (Irsyad, 2026-11-06); job and spec without version numbers | `outputs/jobs/seiko-snk381k1/cmp-front.png` |

Not approved yet; not in `models/watches/`.

## Known gaps

- Front photo only: case, lug and bracelet heights are the SNK607K1 values, not measured for this watch.
- The hands' soft shadows stay faintly in the dial map; the 0 of 10 (crossed by the seconds hand) is repaired by mirroring and shows a small seam.
- Bracelet column split and row stagger are read by eye from #1.
