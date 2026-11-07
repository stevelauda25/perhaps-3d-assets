# Sources: CARTIER Santos de Cartier Large WSSA0062

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `cartier-wssa0062_original.jpg` | Cartier catalogue photo linked from the "View photo" cell of catalog 2 (row 40, WSSA0062): `https://www.cartier.com/dw/image/v2/BGTJ_PRD/on/demandware.static/-/Sites-cartier-master/default/dwae56efa3/images/large/5422c5fc673d5f9a8a41a1aecb8a87fa.png?sw=750&sh=750&sm=fit&sfrm=png` | 750 x 750 JPEG, near-white background (247,249,250 at the top corners, 228,233,234 at the bottom corners) with a soft shadow gradient and a thin white halo around the case, NO alpha | Original, untouched. |
| `cartier-wssa0062_1500x1500.png` | Working copy of the above | 1500 x 1500 | 2x Lanczos4 (OpenCV) by `pipeline/cartier_santoslarge_prep.py wssa0062` (the prep takes the SKU as its argument, so no variant-named copy was needed). Enlargement for inspection and sampling only: no recovered detail. |
| `outputs/watches/cartier-santoslarge-wssa0062/silhouette_mask.png` | Derived by the prep script (not a download) | 750 x 750, 8-bit soft alpha | Flood fill from the border with a neighbour-to-neighbour tolerance of 5 grey levels (6 removes 3,663 px at the bright top bracelet edge on this photo, as on the blue one; 4 differs from 5 by 296 px = the case's light halo), close 3x3, fill holes, largest component, median 3x3, Gaussian 0.7 px; silhouette = alpha above half. Checked on gridded 4x overlays at the four corners, the top and bottom bracelet and the crown (within 1 to 2 px of the dark case outline; a light halo remains around the crown dome). |

Catalog 2 line: Cartier, Santos de Cartier Large Green, WSSA0062, 39.8mm, Steel, green, Bracelet, Brand New, 8740 / 9200.
Cartier image rights remain with the manufacturer; reference use only.
