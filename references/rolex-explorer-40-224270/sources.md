# Sources: ROLEX Explorer 40 224270 (40 mm steel, black dial, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-224270_original.png` | Rolex official product render from the Rolex image host (the Catalog 2 workbook has no photo link for the Rolex rows; the lead took one upright render per row with the user's approval): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m224270-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render, one camera for all models; the watch occupies x 514..1478, y 683..2513, i.e. 965 x 1831 px incl. the crown) | Original, untouched; downloaded by the lead. |

No enlargement copy: at 22.25 px/mm the render is already sharp, so everything is measured and mapped at native size (the dial map is a native crop, 792 x 792 px; the steel map is the whole watch at native size, 973 x 1839 px, so the 2048 px cap does not bite and the map scale is 1.0; both are written by `pipeline/rolex_explorer40_prep.py` to `outputs/watches/rolex-explorer40-224270/`; the comparison render is made at half the native scale and compared with the render downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 45): Rolex, Explorer 40, 224270, 40mm. The render shows a black dial with white numerals 3 / 6 / 9, a white triangle at 12 and white baton indices, the white ROLEX wordmark with crown, "OYSTER PERPETUAL", "EXPLORER", "SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED", SWISS MADE, Mercedes hour hand, sword minute hand and a seconds hand with a lume disc, smooth polished bezel, no crown guards visible; the asset follows the photo (no colour variant in the row).
Rolex image rights remain with the manufacturer; reference use only.
