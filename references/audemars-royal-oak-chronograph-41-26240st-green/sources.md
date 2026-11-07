# Sources: AUDEMARS PIGUET Royal Oak Chronograph 41 26240ST (green)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `audemars-26240st-green_original.png` | Audemars Piguet catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 93, 26240ST, "Steel, green"): `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-994?fmt=png-alpha&dpr=off` | 400 x 542 (exactly what the catalog link returns; PNG with alpha, upright render) | Original, untouched. |
| `audemars-26240st-green_1200x1626.png` | The same AP image host and asset asked for a larger rendition (extra URL parameters `&wid=1200&hei=1626`: `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-994?fmt=png-alpha&dpr=off&wid=1200&hei=1626`); downloaded by the lead before this build | 1200 x 1626 (PNG with alpha, the watch occupies x 456..772, y 578..1083) | Working source for all measuring and for the maps. Untouched. |
| `audemars-26240st-green_2400x3252.png` | Working copy of the 1200 x 1626 file | 2400 x 3252 | 2x Lanczos4 (OpenCV), alpha kept, written by `pipeline/audemars_royaloakchrono41_prep.py 26240st-green`. Enlargement for inspection and sampling only: no recovered detail (the watch has 6.93 px/mm in the source). |

Catalog 2 line (row 93): Audemars Piguet, Royal Oak Chronograph 41, 26240ST, 41mm, Steel, green, Bracelet, Pre-owned, 65000 / 68250. The same SKU is row 91 ("Steel, white", photo `standup-1021`), hence the variant key `26240st-green` and the GLB name `audemars-26240st-green.glb`.
Audemars Piguet image rights remain with the manufacturer; reference use only.
