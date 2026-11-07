# Sources: CARTIER Santos de Cartier Large WSSA0071

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `cartier-wssa0071_original.jpg` | Cartier catalogue photo linked from the "View photo" cell of catalog 2 (row 39, WSSA0071): `https://www.cartier.com/dw/image/v2/BGTJ_PRD/on/demandware.static/-/Sites-cartier-master/default/dwec54579f/images/large/0df5608d248d5d3a84c0dcf47fa1a53f.png?sw=750&sh=750&sm=fit&sfrm=png` | 750 x 750 JPEG, near-white background (236,240,241 at the top-left corner) with a soft shadow gradient and a thin white halo around the case, NO alpha | Original, untouched. |
| `cartier-wssa0071_1500x1500.png` | Working copy of the above | 1500 x 1500 | 2x Lanczos4 (OpenCV) by `pipeline/cartier_santoslarge_prep.py wssa0071` (the prep takes the SKU as its argument, so no variant-named copy was needed). Enlargement for inspection and sampling only: no recovered detail. |
| `outputs/watches/cartier-santoslarge-wssa0071/silhouette_mask.png` | Derived by the prep script (not a download) | 750 x 750, 8-bit soft alpha | Flood fill from the border with a neighbour-to-neighbour tolerance of 5 grey levels (6 leaks into the bright top bracelet edge on this photo and removes rows 81..200 of the strap from the mask; 4 differs from 5 by only 394 px, the case's light halo), close 3x3, fill holes, largest component, median 3x3, Gaussian 0.7 px; silhouette = alpha above half. Checked on gridded 2x overlays at the top and bottom bracelet, the horns, the crown and its guards and the left edge (within 1 to 2 px of the dark case outline everywhere; a 1 px light halo remains around the crown dome). |

Catalog 2 line: Cartier, Santos de Cartier Large, WSSA0071, 39.8mm, Steel, blue, Steel bracelet, Brand New, 8740 / 9200.
Cartier image rights remain with the manufacturer; reference use only.
