# Sources: ROLEX Sea-Dweller 126600 (43 mm steel, black dial, black Cerachrom bezel with coin edge, date with Cyclops lens, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126600_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 55, file suffix 0002): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126600-0002` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 465..1544, y 649..2548, i.e. 1080 x 1900 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a black dial with SEA-DWELLER in red, the date window with Cyclops lens at 3, a black ceramic bezel with the 60-minute scale and a coin edge, thick crown guards, and an Oyster bracelet ending in the Glidelock end (matches the tracker row: variant empty / black). |

No enlargement or working copy: at 23.0 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 746 x 746 px; the steel map is the whole watch, 1088 x 1908 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_seadweller43_prep.py` to `outputs/watches/rolex-seadweller43-126600/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 55): Rolex, Sea-Dweller, 126600.
Rolex image rights remain with the manufacturer; reference use only.
