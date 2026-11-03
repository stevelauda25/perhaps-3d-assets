# Textures in use (final assets only)

All CC0 (ambientCG / Poly Haven); each folder's `source.json` records origin, license and checksums.

| Asset | Folder | Maps read |
| --- | --- | --- |
| Spark Box | `sources/ambientcg_paper006_2k` | Color, Roughness, Displacement |
| Wonder Box | `sources/ambientcg_paper002_2k` | Color, Roughness, NormalGL |
| Select Box | `sources/ambientcg_fabric077_2k` | Color, Roughness, NormalGL, Displacement |
| Prestige Box | `sources/ambientcg_leather039_2k` | Color, Roughness, NormalGL, Displacement |
| Icon Box | `../outputs/packaging/icon-v020/textures` (lean 2k maps, force-added to git) | lum, normal, roughness |
| Watch (Speedmaster) | `sources/ambientcg_metal009_2k`, `sources/ambientcg_metal012_1k` | Roughness, NormalGL |

The Icon maps were derived from the Poly Haven `leather_red_02` 8k scan (`sources/polyhaven_leather_red_02_8k/source.json` has the URL and checksums). The
8k PNGs are not kept; download them again to regenerate with `pipeline/lean_leather_maps.py`.
