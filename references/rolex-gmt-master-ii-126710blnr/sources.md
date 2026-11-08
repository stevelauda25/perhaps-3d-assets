# Sources: ROLEX GMT-Master II 126710BLNR (40 mm steel, black dial, blue and black Cerachrom 24 h bezel "Batman", date with Cyclops lens, GMT hand, Jubilee bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126710blnr_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 58): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126710blnr-0002` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 497..1513, y 685..2514, i.e. 1017 x 1830 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a black dial with date window and Cyclops lens at 3, a blue (lower half) and black (upper half) 24 h bezel and a Jubilee bracelet (matches the tracker row: variant Jubilee). |

No enlargement or working copy: at 23.14 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 740 x 740 px; the steel map is the whole watch, 1025 x 1838 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_gmtmaster40_prep.py` to `outputs/watches/rolex-gmtmaster40-126710blnr/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 58): Rolex, GMT-Master II, 126710BLNR, Jubilee.
Rolex image rights remain with the manufacturer; reference use only.
