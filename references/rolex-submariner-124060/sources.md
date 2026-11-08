# Sources: ROLEX Submariner 124060 (41 mm steel, black dial, black Cerachrom bezel, Oyster bracelet, no date)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-124060_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 47): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m124060-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 493..1520, y 671..2525, i.e. 1028 x 1855 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a black dial and a black ceramic bezel (matches the tracker row: no variant). |

No enlargement or working copy: at 22.8 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 722 x 722 px; the steel map is the whole watch, 1036 x 1863 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_submariner41_prep.py` to `outputs/watches/rolex-submariner41-124060/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 47): Rolex, Submariner, 124060.
Rolex image rights remain with the manufacturer; reference use only.
