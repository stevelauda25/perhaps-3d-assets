# Sources: PATEK PHILIPPE Nautilus 5711/1A (40 mm steel, blue dial, steel bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `patek-57111a_original.jpg` | Patek Philippe catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 107, 5711/1A, "Steel, blue", "Bracelet"): `https://static.patek.com/images/articles/face_white/350/5711_1A_010_1.jpg` | 350 x 492 (JPEG, white background, NO alpha; upright studio render, the watch occupies source x 40..315, y 11..470, i.e. 275 x 459 px incl. the crown; a soft drop shadow lies below the bracelet) | Original, untouched; downloaded by the lead. The host serves no larger version (the URL path names the 350 px rendition). |

Working copy: no file is written; `pipeline/patek_nautilus40_prep.py` enlarges the original x4 with Lanczos in memory (working image 1400 x 1968, 26.5 working px per mm = 6.6 source px per mm) and builds the silhouette by a flood fill of the near-white background from the border (tolerance 12, fixed range, 3x3 opening, 0.8 px Gaussian soft edge). The flood fill reads the drop shadow below the bracelet as foreground, so `measure.mask.clip` cuts the bracelet below working row 1700 along two hand-measured edge lines and at row 1882 (recorded in `config/watches/patek-nautilus40-57111a-measure.json`). Enlargement does not recover detail: geometry, joints and the silhouette can be measured to about +-1 source px (+-0.15 mm), the dial print, hands, indices and brushed grain are only as sharp as the 350 px photo.

Maps written by the prep to `outputs/watches/patek-nautilus40-57111a/`: `dial_photo.jpg` (720 px crop of the x4 working image, equal to 2.7 maps per source px: no extra detail, smooth) and `steel_photo.jpg` (the whole watch, capped at 1400 px on the long side = 3x the source).

Catalog 2 line (row 107): Patek Philippe, Nautilus, 5711/1A, 40mm, Steel, blue, Bracelet, Pre-owned, 145000 / 152250. The photo shows a blue gradient horizontally embossed dial; the asset follows the photo.
Patek Philippe image rights remain with the manufacturer; reference use only.
