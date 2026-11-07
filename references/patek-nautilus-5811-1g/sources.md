# Sources: PATEK PHILIPPE Nautilus 5811/1G (41 mm white gold, blue dial, white gold bracelet)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `patek-58111g_original.png` | Patek Philippe catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 111, 5811/1G, "White gold, bracelet"): `https://patek-res.cloudinary.com/dfsmedia/0906caea301d42b3b8bd23bd656d1711/4827-51887?format=png` | 1920 x 2691 (RGBA PNG with real transparency, upright studio render; the watch occupies x 271..1671, y 261..2551, i.e. 1401 x 2291 px incl. the crown; a faint drop shadow below the bracelet has alpha below half and is not part of the silhouette) | Original, untouched; downloaded by the lead. |

No enlargement copy: at about 33.56 px/mm the photo is already large and sharp, so everything is measured and mapped at native size (the dial map is a native crop, 940 x 940 px; the steel map is the whole watch capped at 2048 px on the long side, i.e. scaled 0.891 from the 2291 px native height with INTER_AREA, 1255 x 2048; both are written by `pipeline/patek_nautilus41_prep.py` to `outputs/watches/patek-nautilus41-58111g/`; the comparison render is made at half the native scale and compared with the photo downscaled by 0.5, INTER_AREA).

Catalog 2 line (row 111): Patek Philippe, Nautilus, 5811/1G, 41mm, White gold, bracelet, Brand New, 245000 / 257250. The photo shows a blue gradient dial (the row text does not state the dial colour); the asset follows the photo.
Patek Philippe image rights remain with the manufacturer; reference use only.
