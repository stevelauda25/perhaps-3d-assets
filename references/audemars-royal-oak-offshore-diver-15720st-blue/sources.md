# Sources: AUDEMARS PIGUET Royal Oak Offshore Diver 15720ST (blue)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `audemars-15720st-blue_original.png` | Audemars Piguet catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 78, 15720ST, "Steel, blue"): `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1339?fmt=png-alpha&dpr=off` | 400 x 542 (exactly what the catalog link returns; PNG with alpha, upright render) | Original, untouched. |
| `audemars-15720st-blue_1200x1626.png` | The same AP image host and asset asked for a larger rendition (extra URL parameters `&wid=1200&hei=1626`: `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1339?fmt=png-alpha&dpr=off&wid=1200&hei=1626`); downloaded by the lead before this build | 1200 x 1626 (PNG with alpha, the watch occupies x 438..783, y 577..1083, i.e. 346 x 507 px) | Working source for all measuring and for the maps. Untouched. |
| `audemars-15720st-blue_2400x3252.png` | Working copy of the 1200 x 1626 file | 2400 x 3252 | 2x Lanczos4 (OpenCV), alpha kept, by `pipeline/audemars_offshorediver42_prep.py 15720st-blue`. Enlargement for inspection and sampling only: no recovered detail (about 6.9 px/mm in the source, 13.8 px/mm in this copy). |

Catalog 2 line (row 78): Audemars Piguet, Royal Oak Offshore Diver, 15720ST, 42mm, Steel, blue, Rubber strap, Pre-owned, 32000 / 33600 (row 77 is the same SKU 15720ST with "Steel, green", photo `standup-717`).
Audemars Piguet image rights remain with the manufacturer; reference use only.
