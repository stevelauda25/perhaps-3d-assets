# Sources: ROLEX GMT-Master II 126720VTNR (40 mm steel, black dial, green and black Cerachrom 24 h bezel "Sprite", left crown, date with Cyclops lens at 9, GMT hand, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126720vtnr_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 57): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126720vtnr-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 406..1422, y 683..2514, i.e. 1017 x 1832 px incl. the crown on the LEFT; one alpha component, no drop shadow) | Original, untouched. The photo shows a black dial, the date window with its Cyclops lens at 9 o'clock, the crown and its guards on the left, a green (lower left) and black 24 h bezel and an Oyster bracelet: this matches the tracker row (variant `left crown / Oyster`); no colour difference. |

No enlargement or working copy: at 23.145 px/mm the render is sharp enough to measure and map at native size (dial map 740 x 740 px, steel map 1025 x 1839 px, both native, scale 1.0, far below the 2048 px cap; both are written by `pipeline/rolex_gmtmaster40_left_prep.py` to `outputs/watches/rolex-gmtmaster40-126720vtnr/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 57): Rolex, GMT-Master II, 126720VTNR, left crown / Oyster.
Rolex image rights remain with the manufacturer; reference use only.
