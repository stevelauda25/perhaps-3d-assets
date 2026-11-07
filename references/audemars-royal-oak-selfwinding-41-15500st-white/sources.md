# Sources: AUDEMARS PIGUET Royal Oak Selfwinding 41 15500ST (white dial)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `audemars-15500st-white_original.png` | Audemars Piguet catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 84, 15500ST, "Steel, white"): `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-996?fmt=png-alpha&dpr=off` | 400 x 542 (exactly what the catalog link returns; PNG with alpha, upright render) | Original, untouched. |
| `audemars-15500st-white_1200x1626.png` | The same AP image host and asset asked for a larger rendition (extra URL parameters `&wid=1200&hei=1626`: `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-996?fmt=png-alpha&dpr=off&wid=1200&hei=1626`); downloaded by the lead before this build | 1200 x 1626 (PNG with alpha, the watch occupies x 457..764, y 577..1083, i.e. 307 x 506 px) | Working source for all measuring and for the maps. Untouched. |
| `audemars-15500st-white_2400x3252.png` | Working copy of the 1200 x 1626 file | 2400 x 3252 | 2x Lanczos4 (OpenCV), alpha kept, by `pipeline/audemars_royaloak41_prep.py 15500st-white`. Enlargement only: no recovered detail (6.95 px/mm in the source, 13.89 px/mm in this copy). |

Catalog 2 line (row 84): Audemars Piguet, Royal Oak Selfwinding 41, 15500ST, 41mm, Steel, white, Bracelet, Pre-owned, 45000 / 47250. Row 89 (SKU 15510ST, "Steel, white", 50000 / 52500) has the very same photo `standup-996`, so this build also serves it under its own file name (the lead publishes the copy).
Audemars Piguet image rights remain with the manufacturer; reference use only.
