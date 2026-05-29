# astrbot_plugin_ark_asa

用于 `ARK: Survival Ascended` 的 AstrBot 本地资料查询插件。

当前支持：

- 生物驯养方式查询
- 生物和物品控制台代码查询
- 材料获取方式查询
- 地图资源点查询
- 地图列表与地图状态查询
- 宝箱与掉落查询
- 统一来源查询
- 列表浏览
- 运行期新增别名

## 常用命令

```text
/ark help
/ark tame 南方巨兽龙
/ark code 霸王龙
/ark item 水泥浆
/ark resource 金属
/ark map 孤岛 水晶
/ark maps
/ark crate 孤岛 红色补给箱
/ark loot 十字弩
/ark source 长管步枪
/ark list creature 高
/ark list item 珍珠
/ark alias 南方巨兽龙 南巨
/ark alias 南方巨兽龙
```

中文快捷命令也可直接使用：

```text
/驯龙 霸王龙
/代码 聚合物
/材料 黑珍珠
/资源 黑曜石
/地图 仙境 金属
/宝箱 畸变 蓝色地表补给箱
/掉落 泵动霰弹枪
/来源 十字弩
/列表 creature 高
/别名 南方巨兽龙 南巨
/别名 南方巨兽龙
```

## 列表功能

支持分类：

- `creature` / `生物` / `恐龙`
- `item` / `物品` / `材料`
- `resource` / `资源`
- `map` / `地图`
- `crate` / `宝箱`

示例：

```text
/ark list creature
/ark list creature 高
/ark list map
/ark list crate 孤岛
```

## 别名功能

运行期新增的别名会写入：

- `data/custom_aliases.json`

支持命令：

```text
/别名 <目标> <别名>
/别名 <目标>
/ark alias add <分类> <目标> = <别名>
/ark alias list <分类> <目标>
```

示例：

```text
/别名 南方巨兽龙 南巨
/别名 南方巨兽龙
/ark alias add creature Acrocanthosaurus = 高棘龙
/ark alias list creature Acrocanthosaurus
```

## AstrBot 配置项

- `max_suggestions`：模糊匹配建议数量
- `show_source_url`：是否显示来源链接
- `max_crate_items_display`：宝箱掉落展示数量
- `show_map_status`：资源查询时是否显示地图状态
- `list_default_limit`：列表默认展示数量
- `allow_runtime_alias_edit`：是否允许运行期新增别名
- `alias_storage_filename`：别名持久化文件名
- `fuzzy_cjk_cutoff`：中文模糊匹配阈值
- `fuzzy_latin_cutoff`：英文模糊匹配阈值

## 数据目录

核心数据位于 `data/`：

- `creatures.json`
- `items.json`
- `resources.json`
- `maps.json`
- `map_aliases.json`
- `creature_spawns.json`
- `loot_crates.json`
- `loot_crate_items.json`
- `item_sources.json`
- `custom_aliases.json`

同步脚本位于 `scripts/sync_wiki.py`。

## 全量恐龙中文补全流程

基于现有 `Dossiers/zh-cn` 页面快照，可以直接重建一轮中文名映射、覆盖率报告和手工补录模板：

```powershell
python C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\scripts\sync_wiki.py autofill-creature-translations `
  --creatures-input C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creatures.generated.json `
  --dossiers-input C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\exports\dossiers_zh_cn.json `
  --manual-overrides C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creature_name_overrides.json `
  --base-map-output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creature_base_zh_map.generated.json `
  --overrides-output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creature_name_overrides.generated.json `
  --translated-output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creatures.generated.zh.json `
  --report-output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creature_translation_report.generated.json `
  --template-output C:\Users\cl\Desktop\ark\astrbot_plugin_ark_asa\data\creature_translation_template.generated.json
```

这一步会输出：

- `creatures.generated.zh.json`：已合并中文名和别名后的全量生物数据
- `creature_translation_report.generated.json`：当前覆盖率和未翻译统计
- `creature_translation_template.generated.json`：剩余未翻译条目的手工补录模板
