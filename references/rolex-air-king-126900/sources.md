# Sources: ROLEX Air-King 126900 (40 mm steel, black dial, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126900_original.png` | Rolex official product render from the Rolex image host (the Catalog 2 workbook has no photo link for the Rolex rows; the lead took one upright render per row with the user's approval): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126900-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render, one camera for all models; the watch occupies x 507..1498, y 687..2514, i.e. 992 x 1828 px incl. the crown) | Original, untouched; downloaded by the lead. |

No enlargement copy: at 22.59 px/mm the render is already sharp, so everything is measured and mapped at native size (the dial map is a native crop, 802 x 802 px; the steel map is the whole watch at native size, 1000 x 1836 px, so the 2048 px cap does not bite and the map scale is 1.0; both are written by `pipeline/rolex_airking_prep.py` to `outputs/watches/rolex-airking-126900/`; the comparison render is made at half the native scale and compared with the render downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 38): Rolex, Air-King, 126900, 40mm, Black, Bracelet, Brand New. The render shows a black dial with white numerals (the Air-King's 5-minute numerals 55 / 05 / 50 / 10 / 9 / 3 / 40 / 20 / 35 / 25 / 6, a white triangle at 12), green and yellow Rolex wordmark and crown, a green seconds hand with a lume dot and a green head disc; the asset follows the photo (it agrees with the row colour "Black").
Rolex image rights remain with the manufacturer; reference use only.
