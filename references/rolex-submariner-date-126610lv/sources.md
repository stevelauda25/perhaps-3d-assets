# Sources: ROLEX Submariner Date 126610LV (41 mm steel, black dial, green Cerachrom bezel, date with Cyclops lens, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126610lv_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 49): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126610lv-0002` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 493..1520, y 671..2525; the alpha mask equals the 126610LN's: 0 px differ by more than 60/255, max 10) | Original, untouched. The photo shows a black dial with the date window and Cyclops lens at 3 and a GREEN ceramic bezel (matches the tracker row: variant black / green bezel). |

No enlargement or working copy: native size; the dial map (722 x 722) and steel map (1036 x 1863, scale 1.0, under the 2048 px cap) are written by `pipeline/rolex_submarinerdate41_prep.py 126610lv` to `outputs/watches/rolex-submarinerdate41-126610lv/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA.

Catalog 2 line (tracker row position 49): Rolex, Submariner Date, 126610LV, black / green bezel.
Rolex image rights remain with the manufacturer; reference use only.
