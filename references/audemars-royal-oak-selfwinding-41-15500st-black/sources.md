# Sources: AUDEMARS PIGUET Royal Oak Selfwinding 41 15500ST (black dial)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `audemars-15500st-black_original.png` | Audemars Piguet catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 83, 15500ST, "Steel, black"): `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1060?fmt=png-alpha&dpr=off` | 400 x 542 (exactly what the catalog link returns; PNG with alpha, upright render) | Original, untouched. |
| `audemars-15500st-black_1200x1626.png` | The same AP image host and asset asked for a larger rendition (extra URL parameters `&wid=1200&hei=1626`: `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1060?fmt=png-alpha&dpr=off&wid=1200&hei=1626`); downloaded by the lead before this build | 1200 x 1626 (PNG with alpha, the watch occupies x 456..765.8, y 578..1083, i.e. 310 x 506 px) | Working source for all measuring and for the maps (verified to hold real extra detail, not just resampling). Untouched. |
| `audemars-15500st-black_2400x3252.png` | Working copy of the 1200 x 1626 file | 2400 x 3252 | 2x Lanczos4 (OpenCV), alpha kept, by `pipeline/audemars_royaloak41_prep.py`. Enlargement for inspection and sampling only: no recovered detail (the watch has 7.01 px/mm in the source, 14.03 px/mm in this copy). |

Catalog 2 line: Audemars Piguet, Royal Oak Selfwinding 41, 15500ST, 41mm, Steel, black, Bracelet, Pre-owned, 45000 / 47250 (rows 84 and 85 are the same SKU 15500ST with "Steel, white" / "Steel, grey", photos `standup-996` / `standup-1014`; row 88 is SKU 15510ST "Steel, black" with the very same photo `standup-1060`, so this build also serves it under its own file name).
Audemars Piguet image rights remain with the manufacturer; reference use only.
