# Sources: ROLEX Sea-Dweller Deepsea 136660 D-Blue (44 mm steel, black-to-deep-blue gradient dial, black Cerachrom Ringlock bezel with coin edge, date without Cyclops, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-136660_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 56, file suffix 0005): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m136660-0005` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 463..1565, y 636..2560, i.e. 1103 x 1925 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a black-to-deep-blue gradient dial (blue at the top, black below), DEEPSEA in green, the date window with the 28 at 3 (no Cyclops lens), a black ceramic bezel with the 60-minute scale and a coin edge (a large white reflection covers part of the ceramic), crown guards, and an Oyster bracelet ending in a flat Glidelock end (matches the tracker row: variant D-Blue). |

No enlargement or working copy: at 22.59 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 744 x 744 px; the steel map is the whole watch, 1111 x 1933 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_deepsea44_prep.py` to `outputs/watches/rolex-deepsea44-136660/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 56): Rolex, Sea-Dweller Deepsea, 136660, 'D-Blue'.
Rolex image rights remain with the manufacturer; reference use only.
