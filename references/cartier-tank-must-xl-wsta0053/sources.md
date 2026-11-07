# Sources: CARTIER Tank Must Extra-Large Automatic WSTA0053

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `cartier-wsta0053_original.jpg` | Cartier catalogue photo linked from the "View photo" cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 29, WSTA0053): `https://www.cartier.com/dw/image/v2/BGTJ_PRD/on/demandware.static/-/Sites-cartier-master/default/dwc5ae60fd/images/large/7275b483f0e258299aaf9cf59301208f.png?sw=750&sh=750&sm=fit&sfrm=png` | 750 x 750 JPEG, near-white background with a soft shadow gradient, NO alpha | Original, untouched. |
| `cartier-wsta0053_1500x1500.png` | Working copy of the above | 1500 x 1500 | 2x Lanczos4 (OpenCV) by `pipeline/cartier_tankmustxl_prep.py wsta0053`. Enlargement for inspection and sampling only: no recovered detail. |
| `outputs/watches/cartier-tankmustxl-wsta0053/silhouette_mask.png` | Derived by the prep script (not a download) | 750 x 750, 8-bit soft alpha | Flood fill from the border with a neighbour tolerance of 4 grey levels, close 3x3, fill holes, largest component, median 3x3, Gaussian 0.7 px; silhouette = alpha above half. Checked on the case, the bracelet ends and the crown (the translucent sapphire edge and the shadow beside the crown are the weak spots, a pixel or two). |

Catalog 2 line: Cartier, Tank Must Extra-Large Automatic, WSTA0053, 41x31mm, Steel, silver, Bracelet, Brand New, 5750 / 6050.
Cartier image rights remain with the manufacturer; reference use only.
