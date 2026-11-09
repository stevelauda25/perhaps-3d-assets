# Sources: ROLEX Submariner Date 116610LV "Hulk" (40 mm, green dial, green Cerachrom bezel)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `rolex-116610lv_original.png` | Retailer wristcheck.com listing "submariner-date-stainless-steel-green-dial-116610lv-0002" (gallery image 5), taken by the lead (the Rolex image host has no file for the discontinued 116610LV): `https://res.cloudinary.com/wc-photo/image/upload/c_fill,w_3000,h_3000,g_auto/c_limit,w_2880/f_auto/q_auto/v1698409912/cms/BUY/Inventory/Rolex/W01269_RLX_116610LV/01_Product_Photo/W01269_RLX_001_d0320ca7eb` | 2880 x 2880 RGBA PNG with real transparency; the watch (bbox x 722..2292, y 193..2705) is NOT centred, the bracelet is cut by the image at both ends | Original, untouched, no working copy; somewhat soft (upscaled by the retailer, no invented sharpness). Pre-owned-listing image, possibly the retailer's copyright: reference use only. |

Maps (written by `pipeline/rolex_submarinerdate40_prep.py 116610lv` to `outputs/watches/rolex-submarinerdate40-116610lv/`): dial map native crop, steel map the photo bbox downscaled to the 2048 px cap (scale recorded in its json); the comparison render is made at half the native scale (17.8 px/mm) and compared with the photo downscaled by 0.5, INTER_AREA.

Catalog 2 line (tracker row position 52): Rolex, Submariner Date, 116610LV, green.
