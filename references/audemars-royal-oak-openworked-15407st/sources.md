# Sources: AUDEMARS PIGUET Royal Oak Double Balance Wheel Openworked 41 15407ST (steel, skeleton dial)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `audemars-15407st_original.png` | Audemars Piguet catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 108, 15407ST, "Stainless steel, skeleton"): `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1233?fmt=png-alpha&dpr=off` | 400 x 542 (exactly what the catalog link returns; PNG with alpha, upright render) | Original, untouched. |
| `audemars-15407st_1200x1626.png` | The same AP image host and asset asked for a larger rendition (extra URL parameters `&wid=1200&hei=1626`: `https://dynamicmedia.audemarspiguet.com/is/image/audemarspiguet/standup-1233?fmt=png-alpha&dpr=off&wid=1200&hei=1626`); downloaded by the lead before this build | 1200 x 1626 (PNG with alpha, the watch occupies x 457..766, y 578..1083, i.e. 310 x 506 px) | Working source for all measuring and for the maps (real extra detail, not just resampling). Untouched. The skeleton dial is partly see-through in this file (alpha below 255 in the cut-outs of the movement, about 1,260 px below half alpha inside the dial). |
| `audemars-15407st_2400x3252.png` | Working copy of the 1200 x 1626 file | 2400 x 3252 | 2x Lanczos4 (OpenCV), alpha kept, by `pipeline/audemars_royaloakopenworked41_prep.py`. Enlargement for inspection and sampling only: no recovered detail (the watch has 7.0 px/mm in the source, 14.0 px/mm in this copy). |

Catalog 2 line: Audemars Piguet, Royal Oak Double Balance Wheel Openworked 41, 15407ST, 41mm, "Stainless steel, skeleton", Bracelet, Pre-owned, 155000 / 162750 (row 108).
Audemars Piguet image rights remain with the manufacturer; reference use only.
