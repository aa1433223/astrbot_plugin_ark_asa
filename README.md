# astrbot_plugin_ark_asa

用于 `ARK: Survival Ascended` 的 AstrBot 本地资料查询插件。

当前支持：
- 生物驯养方式查询
- 生物与物品控制台代码查询
- 材料获取方式查询
- 地图资源点查询
- 地图列表与状态查询
- 宝箱与掉落查询
- 统一来源查询
- 列表浏览与翻页
- 运行期自定义别名
- LLM 智能问答联动

## 命令总览

### 一级命令入口

```text
/ark
/方舟
/驯龙
/代码
/材料
/资源
/地图
/宝箱
/掉落
/来源
/列表
/别名
/地图列表
/方舟问答
/arkai
```

### `/ark` 子命令

```text
/ark help
/ark tame <生物名>
/ark code <生物名或物品名>
/ark item <物品名>
/ark resource <资源名>
/ark map <地图名> [资源名]
/ark maps [地图名]
/ark crate <地图名> <宝箱名>
/ark loot <物品名>
/ark source <物品名>
/ark list <分类> [关键字] [页码]
/ark alias <目标> [别名]
/ark alias add <分类> <目标> = <别名>
/ark alias list <分类> <目标>
/ark ai <问题>
/ark ask <问题>
/ark chat <问题>
```

### `/方舟` 支持的中文子命令

```text
/方舟 帮助
/方舟 驯养 <生物名>
/方舟 驯龙 <生物名>
/方舟 代码 <生物名或物品名>
/方舟 材料 <物品名>
/方舟 资源 <资源名>
/方舟 地图 <地图名> [资源名]
/方舟 地图列表 [地图名]
/方舟 宝箱 <地图名> <宝箱名>
/方舟 掉落 <物品名>
/方舟 来源 <物品名>
/方舟 列表 <分类> [关键字] [页码]
/方舟 别名 <目标> [别名]
/方舟 问答 <问题>
/方舟 智能 <问题>
/方舟 智能问答 <问题>
```

### 中文快捷命令

```text
/驯龙 <生物名>
/代码 <生物名或物品名>
/材料 <物品名>
/资源 <资源名>
/地图 <地图名> [资源名]
/宝箱 <地图名> <宝箱名>
/掉落 <物品名>
/来源 <物品名>
/列表 <分类> [关键字] [页码]
/别名 <目标> [别名]
/地图列表 [地图名]
/方舟问答 <问题>
/arkai <问题>
```

## 常用示例

```text
/ark help
/ark tame 南方巨兽龙
/ark code 高棘龙
/ark item 水泥膏
/ark resource 黑曜石
/ark map 孤岛 水晶
/ark maps
/ark crate 孤岛 红色补给箱
/ark loot 十字弩
/ark source 长管步枪
/ark ai 高棘龙怎么驯
/方舟问答 泰克步枪从哪里出
```

## 列表功能与翻页

支持分类：
- `creature` / `creatures` / `dino` / `生物` / `恐龙`
- `item` / `items` / `物品` / `材料` / `道具`
- `resource` / `resources` / `资源`
- `map` / `maps` / `地图`
- `crate` / `crates` / `lootcrate` / `宝箱` / `补给箱`

翻页规则：
- 格式为 `/ark list <分类> [关键字] [页码]`
- 最后一个纯数字会被识别为页码
- 每页条数由 AstrBot 配置项 `list_default_limit` 控制
- 返回结果里会自动附带“上一页 / 下一页”提示命令

示例：

```text
/ark list creature
/ark list creature 2
/ark list creature 高 2
/ark list item 珍珠
/ark list resource 金属 3
/ark list map
/ark list crate 孤岛 2
/列表 生物 2
/列表 宝箱 孤岛 3
```

## 别名功能

运行期新增的别名会写入：

- `data/custom_aliases.json`

支持命令：

```text
/别名 <目标> <别名>
/别名 <目标>
/ark alias <目标> <别名>
/ark alias <目标>
/ark alias add <分类> <目标> = <别名>
/ark alias list <分类> <目标>
```

示例：

```text
/别名 南方巨兽龙 南巨
/别名 南方巨兽龙
/ark alias 高棘龙 高刺龙
/ark alias add creature Acrocanthosaurus = 高棘龙
/ark alias list creature Acrocanthosaurus
```

说明：
- 简写 `/别名 南方巨兽龙 南巨` 会自动推断目标分类
- 简写 `/别名 南方巨兽龙` 会直接查看这个目标当前已有的别名
- 如果同名目标命中了多个分类，插件会提示你改用显式写法

## 智能问答

当 `enable_llm_query=true` 时，可以通过以下命令调用当前会话模型，让插件先检索本地资料再交给 LLM 组织答案：

```text
/ark ai <问题>
/ark ask <问题>
/ark chat <问题>
/方舟问答 <问题>
/arkai <问题>
/方舟 问答 <问题>
/方舟 智能 <问题>
/方舟 智能问答 <问题>
```

示例：

```text
/ark ai 高棘龙驯服方式和推荐食物
/ark ask 孤岛前期金属矿主要分布在哪
/方舟问答 泰克步枪可能从哪些宝箱出
```

## AstrBot 配置项

- `max_suggestions`：模糊匹配候选数量
- `show_source_url`：是否显示 Wiki 来源链接
- `max_crate_items_display`：宝箱掉落展示数量
- `show_map_status`：资源查询时是否显示地图状态
- `list_default_limit`：列表每页显示数量
- `allow_runtime_alias_edit`：是否允许运行期新增别名
- `alias_storage_filename`：别名持久化文件名
- `fuzzy_cjk_cutoff`：中文模糊匹配阈值
- `fuzzy_latin_cutoff`：英文模糊匹配阈值
- `enable_llm_query`：是否启用 LLM 智能问答
- `llm_query_provider_id`：指定用于问答的 Provider ID，留空则跟随当前会话
- `llm_query_max_context_chars`：传给 LLM 的本地资料最大字符数
- `llm_query_max_sections`：传给 LLM 的本地资料最大段数
- `llm_query_system_prompt`：LLM 智能问答系统提示词

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

这一阶段会输出：
- `creatures.generated.zh.json`：合并中文名和别名后的全量生物数据
- `creature_translation_report.generated.json`：当前覆盖率和未翻译统计
- `creature_translation_template.generated.json`：剩余未翻译条目的手工补录模板
