# Sources: ROLEX Sky-Dweller 336934 (42 mm steel, white-gold fluted bezel, blue dial, annual calendar ring, Cyclops date, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-336934_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 65, host file suffix 0005): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m336934-0005` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 479..1511, y 659..2537, i.e. 1033 x 1879 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a blue sunburst dial with applied baton indices (12 as a square), the annual calendar ring with 24 h numerals and a red pointer at 8 o'clock, a Cyclops date at 3, a white-gold fluted bezel and an Oyster bracelet (matches the tracker row "blue"; Oyster, not Jubilee). |

No enlargement or working copy: at 22.9 px/mm the render is sharp enough to measure and map at native size (dial map 754 x 754 px, steel map the whole watch 1041 x 1887 px, both native, scale 1.0, well under the 2048 px cap; written by `pipeline/rolex_skydweller42_prep.py` to `outputs/watches/rolex-skydweller42-336934/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 65): Rolex, Sky-Dweller, 336934, "blue".
Rolex image rights remain with the manufacturer; reference use only.
