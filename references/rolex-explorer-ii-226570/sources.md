# Sources: ROLEX Explorer II 226570 (42 mm steel, white dial, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-226570_original.png` | Rolex official product render from the Rolex image host (the Catalog 2 workbook has no photo link for the Rolex rows; the lead took one upright render per row with the user's approval): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m226570-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render, one camera for all models; the watch occupies x 481..1508, y 660..2537, i.e. 1028 x 1878 px incl. the crown) | Original, untouched; downloaded by the lead. |

No enlargement copy: at 22.64 px/mm the render is already sharp, so everything is measured and mapped at native size (the dial map is a native crop, 786 x 786 px; the steel map is the whole watch at native size, 1036 x 1886 px, so the 2048 px cap does not bite and the map scale is 1.0; both are written by `pipeline/rolex_explorer2_prep.py` to `outputs/watches/rolex-explorer2-226570/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 46): Rolex, Explorer II, 226570, 42mm. The tracker's dial colour is "white or black"; the photo (file suffix 0001) clearly shows a WHITE dial with an orange 24 h (GMT) hand and orange EXPLORER II, so the asset follows the photo. The render shows a fixed matt steel bezel with an engraved 24 h scale, crown guards, date with Cyclops lens at 3, Mercedes hour hand, sword minute hand, seconds hand with a lume ring, orange GMT hand and an Oyster bracelet.
Rolex image rights remain with the manufacturer; reference use only.
