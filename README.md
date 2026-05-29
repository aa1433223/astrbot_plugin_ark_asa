# astrbot_plugin_ark_asa

方舟生存飞升资料查询插件。

这是一个面向 `ARK: Survival Ascended` 的 AstrBot 本地资料查询插件，首版支持：

- 生物驯养方式查询
- 生物和物品控制台代码查询
- 材料获取方式查询
- 地图资源点查询
- 地图列表和地图状态查询
- 宝箱查询
- 物品宝箱掉落反向查询
- 统一来源查询

## 目录

- 插件目录：`astrbot_plugin_ark_asa`
- 建议放入 AstrBot 的插件目录后重载
- 同步脚本：`scripts/sync_wiki.py`

## 支持指令

```text
/ark help
/ark tame 南方巨兽龙
/ark code 霸王龙
/ark item 水泥浆
/ark resource 金属
/ark map 孤岛 水晶
/ark maps
/ark maps 畸变
/ark crate 孤岛 红色补给箱
/ark loot 十字弩
/ark source 泵动霰弹枪

/驯龙 霸王龙
/代码 聚合物
/材料 黑珍珠
/资源 黑曜石
/地图 仙境 金属
/宝箱 畸变 红色地表补给箱
/掉落 霸王龙鞍
/来源 长管步枪
```

## 当前内置内容

- 地图元数据：已扩成 ASA 路线图导向的数据结构，含已上线和计划中地图
- 生物：霸王龙、南方巨兽龙、棘背龙、风神翼龙、阿根廷巨鹰、镰刀龙、羽暴龙、沧龙、迅猛龙、翼龙、甲龙、角龙
- 材料：金属锭、水泥浆、聚合物、有机聚合物、黑珍珠、硅珍珠、石油、水晶、黑曜石、电子元件
- 宝箱与掉落：已加入一批可运行的示例数据，用来支撑 `/ark crate`、`/ark loot`、`/ark source`

## 扩展方式

后续补内容时，优先直接维护 `data` 目录里的 JSON：

- `data/creatures.json`
- `data/items.json`
- `data/resources.json`
- `data/map_aliases.json`
- `data/maps.json`
- `data/creature_spawns.json`
- `data/loot_crates.json`
- `data/loot_crate_items.json`
- `data/item_sources.json`

字段已经尽量保持结构化，继续扩展时直接照现有格式追加即可。

## 同步思路

推荐路线是：

1. 用 `scripts/sync_wiki.py` 探测 `wiki.gg` 的 Cargo 表
2. 能走 API 的内容优先走 `cargoquery`
3. 地图资源页、宝箱页等结构不稳定内容做离线抓取或手工修正
4. 最终把同步结果整理回 `data/*.json`

脚本当前已提供：

- Cargo 表探测
- Cargo 字段探测
- Cargo 分页导出到 JSON
- ASA 探测快照
- 页面 HTML 拉取
- 批量抓取页面
- 从解析页面抽取 `/wiki/...` 子页面链接
- 从 `loot_crate_items.json` 重建 `item_sources.generated.json`

可以先这样跑：

```powershell
python C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\scripts\sync_wiki.py probe-asa --output-dir C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\sync_probe
python C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\scripts\sync_wiki.py cargo-fields --table 你的表名
python C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\scripts\sync_wiki.py cargo-export --table 你的表名 --fields "field1,field2" --output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\exports\table.json
python C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\scripts\sync_wiki.py cargo-export-preset --preset creatures_core --output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\exports\creatures.json
python C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\scripts\sync_wiki.py build-creatures-dataset --input C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\exports\creatures.json --output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creatures.generated.json
```

## 说明

- 当前版本是本地知识库方案，优点是快、稳定、容易扩充。
- 如果你后续想做在线 Wiki 兜底，可以在 `services` 下再加 provider。
- 当前版本已经把“全恐龙、全地图、全宝箱来源”需要的底座搭好，后续主要是数据补全与同步策略细化。
