# Sources: PATEK PHILIPPE Cubitus 5821/1A (steel, green)

| File | Source | Pixels | Notes |
| --- | --- | --- | --- |
| `patek-58211a_original.png` | Patek Philippe catalogue photo linked from the photo cell of catalog 2 (`CJW_x_Rare_Treat_Catalog (2).xlsx`, row 103, 5821/1A, "Steel, green"): `https://patek-res.cloudinary.com/dfsmedia/0906caea301d42b3b8bd23bd656d1711/185659-51887?format=png` | 1920 x 2691 (RGBA PNG with real transparency, upright studio render; the watch occupies x 295..1699, y 247..2560, i.e. 1405 x 2314 px incl. the crown; a faint drop shadow below the bracelet has alpha below half and is not part of the silhouette) | Original, untouched; downloaded by the lead. |

No enlargement copy: at about 30.24 px/mm the photo is already large and sharp, so everything is measured and mapped at native size. The dial map is a native-size crop (912 x 912 px); the steel map is the whole watch from the photo, downscaled with INTER_AREA from 1414 x 2321 px to 2048 px on the long side for the mobile target (written by `pipeline/patek_cubitus45_prep.py` to `outputs/watches/patek-cubitus45-58211a/`; `steel_photo.json` "scale" = map px per photo px). The comparison render is made at half the native scale and compared with the photo downscaled by 0.5 (INTER_AREA).

Catalog 2 line (row 103): Patek Philippe, Cubitus, 5821/1A, 45mm, Steel, green, Bracelet, Brand New, 105000 / 110250.
Patek Philippe image rights remain with the manufacturer; reference use only.
