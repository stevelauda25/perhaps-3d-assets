# Sources: CARTIER Santos de Cartier Large WSSA0018

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `cartier-wssa0018_original.jpg` | Cartier catalogue photo linked from the "View photo" cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 38, WSSA0018): `https://www.cartier.com/dw/image/v2/BGTJ_PRD/on/demandware.static/-/Sites-cartier-master/default/dwe0571f8e/images/large/dc3bdd3c05f257f5b216fc83a0a73794.png?sw=750&sh=750&sm=fit&sfrm=png` | 750 x 750 JPEG, near-white background with a soft shadow gradient and a thin white halo around the case, NO alpha | Original, untouched. |
| `cartier-wssa0018_1500x1500.png` | Working copy of the above | 1500 x 1500 | 2x Lanczos4 (OpenCV) by `pipeline/cartier_santoslarge_prep.py wssa0018`. Enlargement for inspection and sampling only: no recovered detail. |
| `outputs/watches/cartier-santoslarge-wssa0018/silhouette_mask.png` | Derived by the prep script (not a download) | 750 x 750, 8-bit soft alpha | Flood fill from the border with a neighbour-to-neighbour tolerance of 6 grey levels (3 or 4 as on the Tank leaves the case's white halo in the mask, 7 and above leaks into the bright strap edge), close 3x3, fill holes, largest component, median 3x3, Gaussian 0.7 px; silhouette = alpha above half. Checked on a gridded overlay at the horns, the crown and guards, the bracelet ends and the strap edges (within 1 to 2 px of the dark case outline everywhere). |

Catalog 2 line: Cartier, Santos de Cartier Large, WSSA0018, 39.8mm, Steel, silver, Bracelet, Brand New, 8740 / 9200.
Cartier image rights remain with the manufacturer; reference use only.
