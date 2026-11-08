# Sources: ROLEX Submariner Date 126610LN (41 mm steel, black dial, black Cerachrom bezel, date with Cyclops lens, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126610ln_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 48): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126610ln-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 493..1520, y 671..2525, i.e. 1028 x 1855 px incl. the crown; one alpha component, no drop shadow; the alpha mask is pixel-identical to the no-date 124060's: 0 px differ by more than 60/255) | Original, untouched. The photo shows a black dial with the date window and Cyclops lens at 3 and a black ceramic bezel (matches the tracker row: variant black). |

No enlargement or working copy: at 22.8 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 722 x 722 px; the steel map is the whole watch, 1036 x 1863 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_submarinerdate41_prep.py` to `outputs/watches/rolex-submarinerdate41-126610ln/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 48): Rolex, Submariner Date, 126610LN, black.
Rolex image rights remain with the manufacturer; reference use only.
