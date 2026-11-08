# Sources: ROLEX Datejust 41 126334 (41 mm steel, white-gold fluted bezel, mint green dial, Cyclops date, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126334_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 63, host file suffix 0027): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126334-0027` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 505..1473, y 672..2526, i.e. 969 x 1855 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a mint green sunburst dial with applied baton indices, a date window with a Cyclops at 3 and a white-gold fluted bezel on an Oyster bracelet (matches the tracker row "mint green / Oyster"). |

No enlargement or working copy: at 22.2 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 724 x 724 px; the steel map is the whole watch, 977 x 1863 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_datejust41_prep.py` to `outputs/watches/rolex-datejust41-126334/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 63): Rolex, Datejust 41, 126334, 41mm, "mint green / Oyster".
Rolex image rights remain with the manufacturer; reference use only.
