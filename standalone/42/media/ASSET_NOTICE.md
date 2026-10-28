# ASSET NOTICE — DCWhale 服装素材来源

本目录下的以下文件改编自用户本机已安装的创意工坊 mod **CosplayShop**
（Steam Workshop ID `2707905930`），仅作为本地原型用于打通 B42 服装管线：

| 本项目文件 | 来源文件（CosplayShop） |
|---|---|
| `42/media/models_X/Skinned/Clothes/DCWhaleSailorSuit.FBX` | `42/media/models_X/Skinned/Clothes/I401SailorSuit.FBX` |
| `42/media/models_X/Skinned/Clothes/DCWhaleSailorSkirt.FBX` | `42/media/models_X/Skinned/Clothes/I401SailorSkirt.FBX` |
| `42/media/models_X/Skinned/Clothes/DCWhaleShoes.FBX` | `42/media/models_X/Skinned/Clothes/I401Shoes.FBX` |
| `42/media/textures/Clothes/DCWhale/*.png`、`42/media/textures/Item_DCWhale*.png` | `42/media/textures/Clothes/401/I401*.png` |
| `42/media/clothing/clothingItems/DCWhale*.xml` | 参照 `42/media/clothing/clothingItems/I401*.xml` 结构重写 |
| `42/media/scripts/DC_Whale_Clothing_item.txt` | 参照 `42/media/scripts/I401_Clothing_item.txt` 字段重写 |

约定：

- 所有 GUID 均为新生成，与来源 mod 无冲突；`DCWhaleSailorSkirt` 复用上衣贴图，
  与来源 mod 中裙子复用 `I401SailorSuit` 贴图的做法一致。
- 套装注册名：`DCWhaleGirl`（`42/media/clothing/clothing.xml`）。
- **这些是第三方素材副本，仅限本地测试与管线验证。任何对外发布前必须
  获得原 mod 作者许可或替换为自有美术，并保留原始许可声明。**
  （见 AGENTS.md「依赖与许可证边界」：禁止未经审查把 Workshop 二进制塞入发布包。）
