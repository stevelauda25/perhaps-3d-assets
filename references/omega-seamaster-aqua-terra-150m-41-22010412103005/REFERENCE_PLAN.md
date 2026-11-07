# Reference plan: OMEGA Seamaster Aqua Terra 150M 41 mm 220.10.41.21.03.005 (steel, blue teak-pattern dial, polished fixed bezel, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). It follows the Omega approach of the [Diver 300M rubber build](../omega-seamaster-diver-300m-21032422001001/REFERENCE_PLAN.md) (1024 px PNG with alpha, scale anchored on a measured case dimension, ring centre offset from the pivot) with Aqua Terra specifics, and sets the **Omega Aqua Terra 41 template**.

## Target asset

Front relief GLB `models/watches/omega-22010412103005.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-22010412103005_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Omega Diver 300M build, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 240..819, y 0..1023 (bracelet ends = image borders; crown to x 819) |
| Anchor | the cushion case is NOT a circle (circle fits of the left silhouette have rms 0.4 to 2.5 px depending on the rows): case width = left silhouette minimum 240.26 mirrored about the case axis x = 509.15 -> 537.8 px = 41 mm -> 13.117 px/mm (cross-checks: bracelet 265 px = 20.2 mm at the lugs; bezel top circle 40.2 mm) |
| Pivot | hour, minute and seconds axes cross at (508.62, 470.96) (hand height, residuals 0.0 / 0.23 / 0.22 px); angles 304.07 / 47.75 / 221.87 deg (10:08:36) |
| Rings (r px) | dial_flat 211 (end of the blue dial), crystal_edge 223.5, bezel_in 224.0 (bright inner rim, circle centre (510.27, 471.27)), bevel to r 235.5, bezel_out = outer edge of the polished top 263.8 (circle centre (509.37, 472.94), rms 0.53), case flank beyond it to the silhouette r ~ 269; one ring centre (509.75, 472.05) = `ring_centre_mm` [0.086, -0.083] |
| Bezel | fixed polished steel (no insert, no markings); inner bevel, then a flat polished top |
| Crown | x 776..819.5, y 436..521 (85 px = 6.5 mm, centre 478.5), fluted to x 800 then a rounded cap with a round boss; no crown housing shoulder |
| Lugs | integral with the case: tops y 174, bottoms y 795; bracelet width 265 px (20.2 mm) at the lugs, 231 px at the top image border, 241 px at the bottom |
| Bracelet | three columns: brushed outer links with stepped dark joints (3 to 21 px) and polished centre links; vertical joints x 437.5 / 579.5 (row 20) ... 432.5 / 578.5 (row 200), 437.5 / 584.5 (row 806) ... 439.5 / 580.5 (row 1018); outer joints top rows 28.5, 79..87, 163..179, bottom 771..792, 875..891, 952..963, 1004..1010; centre joints top rows 9, 56, 128..133, 190, bottom 752, 816..824, 908..916, 980 |
| Hands (about 10:08:36) | hour 304.07 deg solid sword, length 121 px, lume strip s 19..76, short triangular tail; minute 47.75 deg solid sword with an arrow head, length 184 px, lume triangle in the head; seconds 221.87 deg thin shaft, lume arrow at s 136..170, needle to 205 px |
| Dial | blue gradient teak (horizontal grooves) dial, applied faceted indices with lume, date window at 6 (x 495..526, y 602..642), minute track on a grey translucent outer ring, all part of the 2x dial photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_omega_aquaterra41.py` of the Omega Diver step (bracelet kind also honours `edge_from`) |
| Prep | `pipeline/omega_aquaterra41_prep.py` (copy of the Omega Diver prep; scale from the case width, crown rows mirrored about the case axis) |
| Comparison frame | 2048 px square = the frame of the 2x photo (pivot (508.62, 470.96) -> (1017.24, 941.92)), camera 26.2342 px/mm, `config/presets/watch_kit_white_front_omega_aquaterra41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_aquaterra41_prep   # -> 2x reference, config/watches/omega-aquaterra41-22010412103005-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
