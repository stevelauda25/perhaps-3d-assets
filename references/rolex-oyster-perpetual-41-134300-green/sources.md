# Sources: ROLEX Oyster Perpetual 41 134300 (41 mm steel, green dial, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-134300-green_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 40): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m134300-0004` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 512..1476, y 673..2525, i.e. 965 x 1853 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a green dial (matches the tracker variant "green"). |

No enlargement or working copy: at 21.8 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 810 x 810 px; the steel map is the whole watch, 973 x 1861 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_oysterperpetual41_prep.py` to `outputs/watches/rolex-oysterperpetual41-134300-green/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 40): Rolex, Oyster Perpetual 41, 134300, 41mm, Green, Bracelet, Brand New.
Rolex image rights remain with the manufacturer; reference use only.
