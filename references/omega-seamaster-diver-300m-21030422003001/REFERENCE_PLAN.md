# Reference plan: OMEGA Seamaster Diver 300M 42 mm 210.30.42.20.03.001 (steel, blue dial with wave pattern, blue ceramic bezel, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). FOLLOWER of the Omega Diver 300M template built for the black rubber version [210.32.42.20.01.001](../omega-seamaster-diver-300m-21032422001001/REFERENCE_PLAN.md): step, prep and kit structure are reused, only the photo-specific values are new.

## Target asset

Front relief GLB `models/watches/omega-21030422003001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, flat front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-21030422003001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the template, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Relation to the rubber photo | same render camera and pose, the whole watch is 0.99577 times smaller about the pivot: left silhouette circle fit r 270.81 px (rubber photo 271.97), ECC affine fit of dial / bezel features 0.9959..0.9962, pivot shift below 0.05 px; the rubber photo's alpha scaled by 0.99577 reproduces this silhouette within 0.2 px over rows 150..780 (case, lugs, crown, helium valve). All case / ring / hand / crown values in mm therefore equal the template's |
| Anchor | circle fitted to the LEFT silhouette (rows 400..600, rms 0.39 px) r 270.81 px = 42 mm / 2 -> 12.8957 px/mm (cross-check: bracelet 20 mm = 257 px = 12.85 px/mm) |
| Pivot | (514.37, 461.4) (template pivot mapped by the ECC fit) |
| Bezel | blue ceramic ring (white numerals, minute dots, lume pip and triangle in the photo), no steel coin ring; ring radii and centre from the template scaled to this photo |
| Hands | the rubber photo's pose (10:09:36-ish): hour 302.3 deg, minute 47.2 deg, seconds 221.6 deg; same skeleton sword hands, lollipop seconds hand with red needle (phase correlation of the dial features 0.04 / 0.07 px) |
| Bracelet | three-link layout, nine columns: outer brushed, polished strip, inner brushed, polished strip, centre brushed, polished strip, inner brushed, polished strip, outer brushed; three staggered joint sets (outer, inner + polished with a wide hinge zone, centre); strip edges (grey > 225) near x 428 / 436 / 462 / 470 / 552 / 560 / 586 / 594 at the top end; width 257 px (19.9 mm) between the lugs; ends at rows 0 (centre) / 4..14 (outer) and 1014..1023 |
| Dial | blue wave pattern, lighter than the black dial of the template (emission checked both ways) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_omega_diver300m.py` read-only (bracelet kind, column driven) |
| Prep | `pipeline/omega_diver300m_prep.py 21030422003001` read-only (it takes the sku as argument; all names derive from it) |
| Comparison frame | 2048 px square = the frame of the 2x photo (pivot (514.37, 461.4) -> (1028.74, 922.8)), camera 25.7914 px/mm, `config/presets/watch_kit_white_front_omega_diver300m_bracelet.json` (the template's kit has 25.902 px/mm and does not fit) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_diver300m_prep 21030422003001   # -> 2x reference, config/watches/omega-diver300m-21030422003001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
