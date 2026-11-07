# Reference plan: OMEGA Seamaster Diver 300M 42 mm 210.32.42.20.01.001 (steel, black dial with wave pattern, black ceramic bezel, black rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). First Omega asset: it sets the Omega Diver 300M approach (structure of the [Breitling Superocean 42 rubber build](../breitling-superocean-42-a17375211b1s1/REFERENCE_PLAN.md), Omega measurements). A later agent builds the bracelet version `210.30.42.20.03.001` (blue) from this template.

## Target asset

Front relief GLB `models/watches/omega-21032422001001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-21032422001001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Breitling / Black Bay 54 builds, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 225..837, y 0..1023 (strap ends = image borders; helium valve to x 225, crown to x 837) |
| Anchor | circle fitted to the LEFT silhouette (case middle, rows 400..600, rms 0.37 px): centre (512.33, 460.66), r 271.97 px = 42 mm / 2 -> 12.951 px/mm (cross-checks: strap 20 mm = 256..258 px, 12.8..12.9 px/mm). The right silhouette is NOT on that circle (visible right flank, crown housing shoulder to x 806) |
| Pivot | hour, minute and seconds axes cross at (514.4, 461.4) (hand height); hub pin hole seen at (514.25, 462.5); bezel top circle centre (511.84, 460.12), inner rim circle centre (511.93, 463.10): tilt parallax; `ring_centre_mm` [-0.19, -0.015] |
| Rings (r px) | dial_flat 189.5, crystal_edge 190.9, bezel_in 191.0 (bright inner rim 191..192.7), bezel_out = ceramic outer edge 257.17 (rms 0.41), case flank beyond it to the silhouette r 272 |
| Bezel | black ceramic ring (white 50/10/20/30/40 numerals, minute dots, lume pip and triangle are print / enamel in the photo), no steel coin ring |
| Crown | x 784..837.6, y 421.8..503.2 (81.4 px = 6.3 mm, centre 462.5), fluted to x 821.7 then a narrower chamfered cap; case housing shoulder to x 806 above / below stays in the silhouette |
| Helium valve | silhouette x 225..~290, rows ~282..372 (10 o'clock), carried by the case silhouette |
| Lugs | tops y 146, bottoms y 782; strap width 256 px (19.8 mm) at the lugs |
| Strap | black rubber, five columns (textured edge, ribbed, textured centre, ribbed, textured edge), four dark grooves 8..10 px wide: x 436/470/550/584 (row 12) ... 425/470/553.5/598.5 (row 140), 426/471.5/552.5/598.5 (row 784) ... 438/469/547.5/580.5 (row 1008) |
| Hands (about 10:06:36) | hour 302.3 deg skeleton sword, length 115.5 px (round lume disc at 93.7 px); minute 47.2 deg skeleton sword, length 167 px (triangle lume tip); seconds 221.6 deg thin shaft, lollipop at 118 px, red needle to 190 px |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_omega_diver300m.py` of the Breitling Superocean step plus: ringless ceramic bezel, skeleton hand parts, crown cap start, generic strap columns |
| Prep | `pipeline/omega_diver300m_prep.py` (copy of the Breitling prep; PNG source, left-silhouette anchor, steel-map crop clamped to the image because the strap leaves the frame) |
| Comparison frame | 2048 px square = the frame of the 2x photo (pivot (514.4, 461.4) -> (1028.8, 922.8)), camera 25.902 px/mm, `config/presets/watch_kit_white_front_omega_diver300m.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_diver300m_prep   # -> 2x reference, config/watches/omega-diver300m-21032422001001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
