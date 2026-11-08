# Sources: ROLEX Yacht-Master 40 126622 (40 mm Rolesium: steel case, platinum bezel, date with Cyclops lens, Oyster bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-126622_original.png` | Rolex official product render from the Rolex image host, downloaded by the lead (Catalog 2 has no photo link for the Rolex rows; row-to-image map `rolex_map.json`, pos 53, file suffix 0001): `https://media.rolex.com/image/upload/c_limit,w_1920/v1/catalogue/2025/upright-c/m126622-0001` | 1920 x 2857 (RGBA PNG with real transparency, upright studio render; the watch occupies x 484..1513, y 679..2514, i.e. 1030 x 1836 px incl. the crown; one alpha component, no drop shadow) | Original, untouched. The photo shows a SLATE (rhodium-grey sunburst) dial with white round lume indices, a long bar at 9 and 6 and a triangle at 12, ROLEX coronet, OYSTER PERPETUAL DATE, cyan YACHT-MASTER, a date window with Cyclops, a cyan seconds hand, a Mercedes-ring hour hand and a platinum bezel. The tracker row says variant "steel / platinum" (the dial colour is not in the tracker text; the photo shows slate). |

No enlargement or working copy: at 23.0 px/mm the render is sharp enough to measure and map at native size (the dial map is a native crop of 716 x 716 px; the steel map is the whole watch, 1038 x 1844 px, native, well under the 2048 px cap, scale 1.0; both are written by `pipeline/rolex_yachtmaster40_prep.py` to `outputs/watches/rolex-yachtmaster40-126622/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (tracker row position 53): Rolex, Yacht-Master 40, 126622, steel / platinum.
Rolex image rights remain with the manufacturer; reference use only.
