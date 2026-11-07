# Sources: AUDEMARS PIGUET Royal Oak Chronograph 41 26240ST (white)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `audemars-26240st-white_original.png` | Audemars Piguet catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 91, 26240ST, "Steel, white"): `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1021?fmt=png-alpha&dpr=off` | 400 x 542 (exactly what the catalog link returns; PNG with alpha, upright render) | Original, untouched. |
| `audemars-26240st-white_1200x1626.png` | The same AP image host and asset asked for a larger rendition (extra URL parameters `&wid=1200&hei=1626`: `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1021?fmt=png-alpha&dpr=off&wid=1200&hei=1626`); downloaded by the lead before this build | 1200 x 1626 (PNG with alpha, the watch occupies x 456..773, y 577..1083, i.e. 318 x 507 px) | Working source for all measuring and for the maps (holds real extra detail, not just resampling). Untouched. |
| `audemars-26240st-white_2400x3252.png` | Working copy of the 1200 x 1626 file | 2400 x 3252 | 2x Lanczos4 (OpenCV), alpha kept, written by `pipeline/audemars_royaloakchrono41_prep.py`. Enlargement for inspection and sampling only: no recovered detail (the watch has 6.93 px/mm in the source, 13.85 px/mm in this copy). |

Catalog 2 line: Audemars Piguet, Royal Oak Chronograph 41, 26240ST, 41mm, Steel, white, Bracelet, Pre-owned, 53000 / 55650 (row 93 is the same SKU 26240ST with "Steel, green", photo `standup-994`).
Audemars Piguet image rights remain with the manufacturer; reference use only.
