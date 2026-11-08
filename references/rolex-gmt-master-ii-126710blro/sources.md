# Sources: ROLEX GMT-Master II 126710BLRO (40 mm steel, black dial, blue and red Cerachrom 24 h bezel "Pepsi", date with Cyclops lens, GMT hand, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126710blro_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 61, file suffix 0002): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126710blro-0002` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 497..1513, y 683..2514, i.e. 1017 x 1832 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a black dial with date window and Cyclops lens at 3, a blue (upper half) and red (lower half) 24 h bezel with a lighter faceted wedge on each colour, a red GMT hand and an Oyster bracelet (matches the tracker row: variant Oyster; the dial colour is black as for the 126710BLNR). |

No enlargement or working copy: at 23.14 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop, the steel map is the whole watch, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_gmtmaster40_prep.py 126710blro` to `outputs/watches/rolex-gmtmaster40-126710blro/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 61): Rolex, GMT-Master II, 126710BLRO, Oyster.
Rolex image rights remain with the manufacturer; reference use only.
