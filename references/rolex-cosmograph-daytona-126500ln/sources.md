# Sources: ROLEX Cosmograph Daytona 126500LN (40 mm steel, white dial with black sub-dial rings, black Cerachrom tachymetre bezel, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126500ln_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 69): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126500ln-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 511..1496, y 682..2513, i.e. 986 x 1832 px incl. the crown and pushers; one alpha component, no drop shadow) | Original, untouched. The photo shows a WHITE dial with BLACK sub-dial rings (the "panda" dial) and a black ceramic bezel with the engraved tachymetre scale, so the tracker's "white or black" resolves to white (the black dial is another reference, 126500LN-0002). |

No enlargement or working copy: at 22.46 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 732 x 732 px; the steel map is the whole watch, 994 x 1840 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_daytona40_prep.py` to `outputs/watches/rolex-daytona40-126500ln/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 69): Rolex, Cosmograph Daytona, 126500LN, white or black.
Rolex image rights remain with the manufacturer; reference use only.
