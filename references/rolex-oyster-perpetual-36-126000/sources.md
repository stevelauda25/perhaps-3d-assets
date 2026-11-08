# Sources: ROLEX Oyster Perpetual 36 126000 (36 mm steel, lavender dial, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126000_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 39): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126000-0013` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 549..1424, y 729..2469, i.e. 876 x 1741 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a lavender (light blue-violet) dial, matching the tracker variant "lavender". |

No enlargement or working copy: at 22.8 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 726 x 726 px; the steel map is the whole watch, 884 x 1749 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_oysterperpetual36_prep.py` to `outputs/watches/rolex-oysterperpetual36-126000/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA). Scale anchor: the listed 36 mm case = 821 px (left flank x 549 to the mirrored right flank about the case centre x 959.5), 22.806 px/mm.

Catalog 2 line (tracker row position 39): Rolex, Oyster Perpetual 36, 126000, 36mm, Lavender, Bracelet, Brand New.
Rolex image rights remain with the manufacturer; reference use only.
