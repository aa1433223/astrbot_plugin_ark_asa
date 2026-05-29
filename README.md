# astrbot_plugin_ark_asa

方舟生存飞升资料查询插件。

这是一个面向 `ARK: Survival Ascended` 的 AstrBot 本地资料查询插件，首版支持：

- 生物驯养方式查询
- 生物和物品控制台代码查询
- 材料获取方式查询
- 地图资源点查询

## 目录

- 插件目录：`astrbot_plugin_ark_asa`
- 建议放入 AstrBot 的插件目录后重载

## 支持指令

```text
/ark help
/ark tame 南方巨兽龙
/ark code 霸王龙
/ark item 水泥浆
/ark resource 金属
/ark map 孤岛 水晶

/驯龙 霸王龙
/代码 聚合物
/材料 黑珍珠
/资源 黑曜石
/地图 仙境 金属
```

## 当前内置内容

- 地图：孤岛、焦土、仙境
- 生物：霸王龙、南方巨兽龙、棘背龙、风神翼龙、阿根廷巨鹰、镰刀龙、羽暴龙、沧龙、迅猛龙、翼龙、甲龙、角龙
- 材料：金属锭、水泥浆、聚合物、有机聚合物、黑珍珠、硅珍珠、石油、水晶、黑曜石、电子元件

## 扩展方式

后续补内容时，优先直接维护 `data` 目录里的 JSON：

- `data/creatures.json`
- `data/items.json`
- `data/resources.json`
- `data/map_aliases.json`

字段已经尽量保持结构化，继续扩展时直接照现有格式追加即可。

## 说明

- 当前版本是本地知识库方案，优点是快、稳定、容易扩充。
- 如果你后续想做在线 Wiki 兜底，可以在 `services/query_service.py` 外再加一个 `providers/wiki_provider.py`。
- 当前回复格式偏纯文本，后面可以继续加文转图卡片。
