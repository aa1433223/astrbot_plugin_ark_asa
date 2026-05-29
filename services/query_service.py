from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class QueryResult:
    message: str
    found: bool = True


def _normalize(text: str) -> str:
    value = (text or "").strip().lower()
    value = re.sub(r"[\s\-_/]+", "", value)
    value = re.sub(r"[^\w\u4e00-\u9fff]", "", value)
    return value


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _join(values: list[str], separator: str = "; ") -> str:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return separator.join(cleaned) if cleaned else "暂无"


class ArkQueryService:
    def __init__(
        self,
        plugin_dir: Path,
        max_suggestions: int = 3,
        show_source_url: bool = True,
        max_crate_items_display: int = 12,
        show_map_status: bool = True,
        list_default_limit: int = 15,
        allow_runtime_alias_edit: bool = True,
        alias_storage_filename: str = "custom_aliases.json",
        fuzzy_cjk_cutoff: float = 0.72,
        fuzzy_latin_cutoff: float = 0.6,
    ):
        self.plugin_dir = plugin_dir
        self.max_suggestions = max(1, max_suggestions)
        self.show_source_url = show_source_url
        self.max_crate_items_display = max(3, max_crate_items_display)
        self.show_map_status = show_map_status
        self.list_default_limit = max(5, list_default_limit)
        self.allow_runtime_alias_edit = allow_runtime_alias_edit
        self.alias_storage_filename = alias_storage_filename.strip() or "custom_aliases.json"
        self.fuzzy_cjk_cutoff = min(0.95, max(0.4, fuzzy_cjk_cutoff))
        self.fuzzy_latin_cutoff = min(0.95, max(0.4, fuzzy_latin_cutoff))

        self.creatures = self._load_merged_dataset(
            "creatures.json",
            "creatures.generated.zh.json",
            key_fields=("name_en", "name_zh", "source_url"),
            fallback_generated_filename="creatures.generated.json",
        )
        self.items = self._load_merged_dataset(
            "items.json",
            "items.generated.json",
            key_fields=("item_code", "name_en", "name_zh", "source_url"),
        )
        self.resources = self._load_json("resources.json")
        self.maps = self._load_json("maps.json")
        self.loot_crates = self._load_json("loot_crates.json")
        self.loot_crate_items = self._load_json("loot_crate_items.json")
        self.item_sources = self._load_merged_dataset(
            "item_sources.json",
            "item_sources.generated.json",
            key_fields=("name_en", "name_zh", "source_url"),
        )
        self.map_aliases = self._load_json("map_aliases.json")
        self.custom_aliases = self._load_alias_store()
        self._apply_custom_aliases()
        self._rebuild_indexes()

    def _load_json(self, filename: str) -> list[dict[str, Any]] | dict[str, list[str]]:
        path = self.plugin_dir / "data" / filename
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_optional_json(self, filename: str) -> list[dict[str, Any]] | dict[str, list[str]] | None:
        path = self.plugin_dir / "data" / filename
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_merged_dataset(
        self,
        manual_filename: str,
        generated_filename: str,
        key_fields: tuple[str, ...],
        fallback_generated_filename: str | None = None,
    ) -> list[dict[str, Any]]:
        manual_rows = self._load_json(manual_filename)
        generated_rows = self._load_optional_json(generated_filename)
        if generated_rows is None and fallback_generated_filename:
            generated_rows = self._load_optional_json(fallback_generated_filename)
        generated_rows = generated_rows or []

        merged: dict[str, dict[str, Any]] = {}
        for row in generated_rows:
            key = self._row_merge_key(row, key_fields)
            if key:
                merged[key] = row

        for row in manual_rows:
            key = self._row_merge_key(row, key_fields)
            if not key:
                continue
            if key in merged:
                merged[key] = self._merge_row_values(merged[key], row)
            else:
                merged[key] = row

        return list(merged.values())

    def _alias_store_path(self) -> Path:
        return self.plugin_dir / "data" / self.alias_storage_filename

    def _load_alias_store(self) -> dict[str, dict[str, list[str]]]:
        default_store = {
            "creature": {},
            "item": {},
            "resource": {},
            "map": {},
            "crate": {},
        }
        raw = self._load_optional_json(self.alias_storage_filename)
        if not isinstance(raw, dict):
            return default_store

        store = dict(default_store)
        for category, values in raw.items():
            if category not in store or not isinstance(values, dict):
                continue
            normalized_values: dict[str, list[str]] = {}
            for key, aliases in values.items():
                if not str(key).strip():
                    continue
                if isinstance(aliases, list):
                    cleaned = []
                    for alias in aliases:
                        alias_text = str(alias).strip()
                        if alias_text and alias_text not in cleaned:
                            cleaned.append(alias_text)
                    if cleaned:
                        normalized_values[str(key).strip()] = cleaned
            store[category] = normalized_values
        return store

    def _save_alias_store(self) -> None:
        path = self._alias_store_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(self.custom_aliases, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def _apply_custom_aliases(self) -> None:
        for category, mapping in self.custom_aliases.items():
            for target_key, aliases in mapping.items():
                self._apply_aliases_for_category(category, target_key, aliases)

    def _rebuild_indexes(self) -> None:
        self.creature_index = self._build_index(self.creatures)
        self.item_index = self._build_index(self.items)
        self.item_source_index = self._build_index(self.item_sources)
        self.map_index = self._build_map_index()
        self.map_display = self._build_display_map(self.maps, primary_key="name_zh", secondary_key="name_en")
        self.resource_index = self._build_resource_index()
        self.resource_display = self._build_resource_display_map()
        self.crate_index = self._build_crate_index()
        self.crate_display = self._build_crate_display_map()
        self.loot_items_by_crate = self._build_loot_items_by_crate()

        self.creature_display = self._build_display_map(self.creatures)
        self.item_display = self._build_display_map(self.items)
        self.item_source_display = self._build_display_map(self.item_sources)

    def _build_index(
        self,
        rows: list[dict[str, Any]],
        primary_key: str = "name_zh",
        secondary_key: str = "name_en",
    ) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for row in rows:
            canonical_names = [row.get(primary_key, ""), row.get(secondary_key, "")]
            alias_names = list(row.get("aliases", []))
            for name in canonical_names:
                key = _normalize(str(name))
                if key:
                    index[key] = row
            for name in alias_names:
                key = _normalize(str(name))
                if key:
                    index.setdefault(key, row)
        return index

    def _build_display_map(
        self,
        rows: list[dict[str, Any]],
        primary_key: str = "name_zh",
        secondary_key: str = "name_en",
    ) -> dict[str, str]:
        display: dict[str, str] = {}
        for row in rows:
            label = row.get(primary_key) or row.get(secondary_key) or "未知条目"
            canonical_names = [row.get(primary_key, ""), row.get(secondary_key, "")]
            alias_names = list(row.get("aliases", []))
            for name in canonical_names:
                key = _normalize(str(name))
                if key:
                    display[key] = str(label)
            for name in alias_names:
                key = _normalize(str(name))
                if key:
                    display.setdefault(key, str(label))
        return display

    def _row_merge_key(self, row: dict[str, Any], key_fields: tuple[str, ...]) -> str:
        for field in key_fields:
            value = row.get(field)
            if value is None or value == "":
                continue
            return _normalize(str(value))
        return ""

    def _merge_row_values(self, base_row: dict[str, Any], override_row: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base_row)
        for key, value in override_row.items():
            if isinstance(value, list):
                existing = merged.get(key, [])
                combined = []
                for item in existing + value:
                    if item not in combined:
                        combined.append(item)
                merged[key] = combined
            elif value not in ("", None, [], {}):
                merged[key] = value
        return merged

    def _dataset_for_category(self, category: str) -> list[dict[str, Any]]:
        mapping = {
            "creature": self.creatures,
            "item": self.items,
            "resource": self.resources,
            "map": self.maps,
            "crate": self.loot_crates,
        }
        return mapping[category]

    def _match_row_for_category(self, category: str, row: dict[str, Any], target_key: str) -> bool:
        normalized_target = _normalize(target_key)
        if not normalized_target:
            return False

        candidate_fields = {
            "creature": ("name_zh", "name_en"),
            "item": ("name_zh", "name_en"),
            "resource": ("resource_name",),
            "map": ("name_zh", "name_en"),
            "crate": ("crate_id", "name_zh", "name_en"),
        }
        for field in candidate_fields.get(category, ()):
            value = row.get(field)
            if _normalize(str(value)) == normalized_target:
                return True

        if category == "resource":
            compound = f"{row.get('map_name', '')}::{row.get('resource_name', '')}"
            return _normalize(compound) == normalized_target
        if category == "crate":
            compound = f"{row.get('map_name', '')}::{row.get('name_zh', '')}"
            return _normalize(compound) == normalized_target
        return False

    def _row_storage_key(self, category: str, row: dict[str, Any]) -> str:
        if category == "resource":
            return f"{row.get('map_name', '')}::{row.get('resource_name', '')}"
        if category == "crate":
            crate_id = str(row.get("crate_id", "")).strip()
            if crate_id:
                return crate_id
            return f"{row.get('map_name', '')}::{row.get('name_zh', '')}"
        return str(row.get("name_en") or row.get("name_zh") or "").strip()

    def _append_aliases_to_row(self, row: dict[str, Any], aliases: list[str]) -> None:
        existing = row.setdefault("aliases", [])
        if not isinstance(existing, list):
            existing = []
            row["aliases"] = existing

        existing_keys = {_normalize(str(alias)) for alias in existing}
        for alias in aliases:
            alias_text = str(alias).strip()
            alias_key = _normalize(alias_text)
            if alias_key and alias_key not in existing_keys:
                existing.append(alias_text)
                existing_keys.add(alias_key)

    def _remove_aliases_from_row(self, row: dict[str, Any], aliases: list[str]) -> None:
        existing = row.get("aliases", [])
        if not isinstance(existing, list):
            return
        alias_keys = {_normalize(str(alias)) for alias in aliases if str(alias).strip()}
        row["aliases"] = [alias for alias in existing if _normalize(str(alias)) not in alias_keys]

    def _apply_aliases_for_category(self, category: str, target_key: str, aliases: list[str]) -> None:
        rows = self._dataset_for_category(category)
        for row in rows:
            if self._match_row_for_category(category, row, target_key):
                self._append_aliases_to_row(row, aliases)

        if category == "item":
            for row in self.item_sources:
                if self._match_row_for_category("item", row, target_key):
                    self._append_aliases_to_row(row, aliases)

    def _remove_aliases_for_category(self, category: str, target_key: str, aliases: list[str]) -> None:
        rows = self._dataset_for_category(category)
        for row in rows:
            if self._match_row_for_category(category, row, target_key):
                self._remove_aliases_from_row(row, aliases)

        if category == "item":
            for row in self.item_sources:
                if self._match_row_for_category("item", row, target_key):
                    self._remove_aliases_from_row(row, aliases)

    def _resolve_category(self, raw_category: str) -> str | None:
        normalized = _normalize(raw_category)
        mapping = {
            "creature": "creature",
            "creatures": "creature",
            "dino": "creature",
            "生物": "creature",
            "恐龙": "creature",
            "龙": "creature",
            "item": "item",
            "items": "item",
            "材料": "item",
            "物品": "item",
            "道具": "item",
            "resource": "resource",
            "resources": "resource",
            "资源": "resource",
            "map": "map",
            "maps": "map",
            "地图": "map",
            "crate": "crate",
            "crates": "crate",
            "lootcrate": "crate",
            "宝箱": "crate",
            "补给箱": "crate",
        }
        return mapping.get(normalized)

    def _build_map_index(self) -> dict[str, dict[str, Any]]:
        index = self._build_index(self.maps)
        for canonical, aliases in self.map_aliases.items():
            row = next((item for item in self.maps if item.get("name_zh") == canonical), None)
            if not row:
                continue
            for alias in aliases:
                key = _normalize(alias)
                if key:
                    index[key] = row
        return index

    def _build_resource_index(self) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = {}
        for row in self.resources:
            canonical_names = [row.get("resource_name", "")]
            alias_names = list(row.get("aliases", []))
            for name in canonical_names:
                key = _normalize(str(name))
                if key:
                    index.setdefault(key, []).append(row)
            for name in alias_names:
                key = _normalize(str(name))
                if key and key not in index:
                    index[key] = [row]
        return index

    def _build_resource_display_map(self) -> dict[str, str]:
        display: dict[str, str] = {}
        for row in self.resources:
            label = str(row.get("resource_name", "未知资源"))
            canonical_names = [row.get("resource_name", "")]
            alias_names = list(row.get("aliases", []))
            for name in canonical_names:
                key = _normalize(str(name))
                if key:
                    display[key] = label
            for name in alias_names:
                key = _normalize(str(name))
                if key:
                    display.setdefault(key, label)
        return display

    def _build_crate_index(self) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = {}
        for row in self.loot_crates:
            canonical_names = [row.get("name_zh", ""), row.get("name_en", ""), row.get("crate_id", "")]
            alias_names = list(row.get("aliases", []))
            for name in canonical_names:
                key = _normalize(str(name))
                if key:
                    index.setdefault(key, []).append(row)
            for name in alias_names:
                key = _normalize(str(name))
                if key and key not in index:
                    index[key] = [row]
        return index

    def _build_crate_display_map(self) -> dict[str, str]:
        display: dict[str, str] = {}
        for row in self.loot_crates:
            label = f"{row.get('map_name', '未知地图')} - {row.get('name_zh', '未知宝箱')}"
            canonical_names = [row.get("name_zh", ""), row.get("name_en", ""), row.get("crate_id", "")]
            alias_names = list(row.get("aliases", []))
            for name in canonical_names:
                key = _normalize(str(name))
                if key:
                    display[key] = label
            for name in alias_names:
                key = _normalize(str(name))
                if key:
                    display.setdefault(key, label)
        return display

    def _build_loot_items_by_crate(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in self.loot_crate_items:
            crate_id = str(row.get("crate_id", "")).strip()
            if crate_id:
                grouped.setdefault(crate_id, []).append(row)
        return grouped

    def help_text(self) -> str:
        return self.help_result().message

    def help_result(self) -> QueryResult:
        return QueryResult(
            "\n".join(
                [
                    "ARK 生存飞升资料查询插件",
                    "",
                    "基础查询：",
                    "/ark tame 南方巨兽龙",
                    "/ark code 霸王龙",
                    "/ark item 水泥浆",
                    "/ark resource 金属",
                    "/ark map 孤岛 水晶",
                    "/ark maps",
                    "",
                    "宝箱与掉落：",
                    "/ark crate 孤岛 红色补给箱",
                    "/ark loot 十字弩",
                    "/ark source 长管步枪",
                    "/ark list creature 高",
                    "/ark alias 南方巨兽龙 南巨",
                    "",
                    "快捷指令：",
                    "/驯龙 霸王龙",
                    "/代码 聚合物",
                    "/材料 黑珍珠",
                    "/资源 黑曜石",
                    "/地图 仙境 金属",
                    "/宝箱 畸变 蓝色地表补给箱",
                    "/掉落 泵动霰弹枪",
                    "/来源 十字弩",
                    "/列表 creature 高",
                    "/别名 南方巨兽龙 南巨",
                    "/地图列表",
                    "",
                    "说明：",
                    "1. 当前插件已经支持地图、宝箱、宝箱掉落、反向来源索引、列表浏览和运行期别名添加。",
                    "2. 运行期新增的别名会写入 data/custom_aliases.json，重启后仍会保留。",
                ]
            )
        )

    def query_tame(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark tame 生物名", found=False)

        creature = self._find_one(raw_query, self.creature_index)
        if not creature:
            return self._not_found("生物", raw_query, self.creature_index, self.creature_display)

        lines = [
            f"生物：{creature['name_zh']} / {creature['name_en']}",
            f"类型：{creature['tame_type']}",
            f"推荐食物：{creature['tame_food']}",
            f"击晕方式：{creature['knockout']}",
            f"鞍具：{creature['saddle']}",
            f"刷新地图：{_join(creature.get('maps', []), ', ')}",
            f"备注：{creature['notes']}",
            f"控制台：admincheat summon {creature['blueprint_path']}",
            f"高等级：admincheat gmsummon \"{creature['blueprint_path']}\" 150",
        ]
        self._append_source(lines, creature)
        return QueryResult("\n".join(lines))

    def query_code(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark code 生物名 或 /ark code 物品名", found=False)

        creature = self._find_one(raw_query, self.creature_index, allow_fuzzy=False)
        if creature:
            lines = [
                f"生物代码：{creature['name_zh']} / {creature['name_en']}",
                f"召唤：admincheat summon {creature['blueprint_path']}",
                f"高等级召唤：admincheat gmsummon \"{creature['blueprint_path']}\" 150",
                f"蓝图路径：{creature['full_blueprint']}",
            ]
            self._append_source(lines, creature)
            return QueryResult("\n".join(lines))

        item = self._find_one(raw_query, self.item_index, allow_fuzzy=False)
        if item:
            lines = [
                f"物品代码：{item['name_zh']} / {item['name_en']}",
            ]
            if str(item.get("item_code", "")).strip():
                lines.append(f"给予物品：admincheat giveitemnum {item['item_code']} 1 0 0")
            lines.append(f"蓝图路径：{item['blueprint_path']}")
            self._append_source(lines, item)
            return QueryResult("\n".join(lines))

        merged_display = self.creature_display | self.item_display
        suggestions = self._suggest_labels(raw_query, self.creature_index | self.item_index, merged_display)
        return self._not_found_text("代码", raw_query, suggestions)

    def query_item(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark item 材料名", found=False)

        item = self._find_one(raw_query, self.item_index)
        if not item:
            return self._not_found("材料", raw_query, self.item_index, self.item_display)

        item_source = self._find_one(raw_query, self.item_source_index)
        lines = [
            f"材料：{item['name_zh']} / {item['name_en']}",
            f"主要获取：{_join(item.get('obtain_methods', []))}",
            f"掉落或采集来源：{_join(item.get('harvest_from', []))}",
            f"推荐工具：{_join(item.get('best_tools', []))}",
            f"备注：{item['notes']}",
        ]
        if str(item.get("item_code", "")).strip():
            lines.insert(4, f"控制台：admincheat giveitemnum {item['item_code']} 1 0 0")
        elif str(item.get("blueprint_path", "")).strip():
            lines.insert(4, f"蓝图路径：{item['blueprint_path']}")

        if item_source:
            crate_names = [entry.get("crate_name", "") for entry in item_source.get("crate_sources", [])]
            if crate_names:
                lines.append(f"相关宝箱：{_join(crate_names)}")

        self._append_source(lines, item)
        return QueryResult("\n".join(lines))

    def query_resource(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark resource 资源名", found=False)

        rows = self._find_resource_rows(raw_query)
        if not rows:
            return self._not_found("资源", raw_query, self.resource_index, self.resource_display)

        lines = [f"资源：{rows[0]['resource_name']}"]
        for row in rows:
            map_text = row["map_name"]
            if self.show_map_status:
                map_row = self._find_one(row["map_name"], self.map_index)
                if map_row:
                    map_text = f"{map_text}（{map_row.get('status', '未知状态')}）"
            lines.append(f"{map_text}：{_join(row.get('areas', []))}")
        lines.append("提示：如需更精确位置，请用 /ark map 地图名 资源名")
        self._append_source(lines, rows[0])
        return QueryResult("\n".join(lines))

    def query_map(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return self.query_maps("")

        parsed = self._split_map_query(raw_query)
        if parsed is None:
            return self.query_map_info(raw_query)

        map_name, resource_name = parsed
        rows = self._find_resource_rows(resource_name, canonical_map=map_name)
        if not rows:
            map_info = self._find_one(map_name, self.map_index)
            status = f"（{map_info.get('status', '未知状态')}）" if map_info else ""
            return QueryResult(
                f"没有找到“{map_name}”{status}中的“{resource_name}”资源资料。你可以先试试：/ark resource {resource_name}",
                found=False,
            )

        row = rows[0]
        lines = [
            f"地图资源：{row['map_name']} - {row['resource_name']}",
            f"推荐区域：{_join(row.get('areas', []))}",
            f"坐标参考：{_join(row.get('coordinates', []))}",
            f"风险提示：{row['risk_level']}",
            f"备注：{row['notes']}",
        ]
        self._append_source(lines, row)
        return QueryResult("\n".join(lines))

    def query_maps(self, raw_query: str) -> QueryResult:
        if raw_query:
            return self.query_map_info(raw_query)

        released = [row["name_zh"] for row in self.maps if row.get("status") == "已上线"]
        upcoming = [row["name_zh"] for row in self.maps if row.get("status") != "已上线"]
        lines = [
            "ARK: Survival Ascended 地图总览",
            f"已上线：{_join(released, ', ')}",
            f"计划中：{_join(upcoming, ', ')}",
            "提示：用 /ark maps 地图名 可查看单张地图详情",
        ]
        return QueryResult("\n".join(lines))

    def query_list(self, raw_query: str) -> QueryResult:
        raw_query = (raw_query or "").strip()
        if not raw_query:
            return QueryResult(
                "\n".join(
                    [
                        "列表用法：",
                        "/ark list creature [关键字]",
                        "/ark list item [关键字]",
                        "/ark list resource [关键字]",
                        "/ark list map [关键字]",
                        "/ark list crate [关键字]",
                    ]
                ),
                found=False,
            )

        parts = raw_query.split(maxsplit=1)
        category = self._resolve_category(parts[0])
        if category is None:
            return QueryResult(f"未识别的列表分类：{parts[0]}", found=False)

        keyword = parts[1].strip() if len(parts) > 1 else ""
        rows = self._list_rows_for_category(category, keyword)
        if not rows:
            return QueryResult(f"没有找到分类 {parts[0]} 下与“{keyword or '全部'}”匹配的条目。", found=False)

        labels = [self._list_label_for_row(category, row) for row in rows[: self.list_default_limit]]
        title_map = {
            "creature": "生物列表",
            "item": "物品列表",
            "resource": "资源列表",
            "map": "地图列表",
            "crate": "宝箱列表",
        }
        lines = [f"{title_map[category]}（共 {len(rows)} 条，显示前 {min(len(rows), self.list_default_limit)} 条）"]
        if keyword:
            lines.append(f"筛选关键字：{keyword}")
        lines.extend(f"- {label}" for label in labels)
        if len(rows) > self.list_default_limit:
            lines.append(f"提示：可在 AstrBot 配置里调大 list_default_limit，当前为 {self.list_default_limit}。")
        return QueryResult("\n".join(lines))

    def query_alias(self, raw_query: str) -> QueryResult:
        raw_query = (raw_query or "").strip()
        if not raw_query:
            return QueryResult(
                "\n".join(
                    [
                        "别名用法：",
                        "/别名 南方巨兽龙 南巨",
                        "/别名 南方巨兽龙",
                        "/ark alias 南方巨兽龙 南巨",
                        "/ark alias add creature Acrocanthosaurus = 高棘龙",
                        "/ark alias list creature Acrocanthosaurus",
                    ]
                ),
                found=False,
            )

        parts = raw_query.split(maxsplit=1)
        action = parts[0].lower()
        rest = parts[1].strip() if len(parts) > 1 else ""

        if action in {"add", "新增", "添加"}:
            return self._handle_alias_add(rest)
        if action in {"list", "show", "查看"}:
            return self._handle_alias_list(rest)
        return self._handle_alias_shorthand(raw_query)

    def _list_rows_for_category(self, category: str, keyword: str) -> list[dict[str, Any]]:
        rows = list(self._dataset_for_category(category))
        if category == "crate":
            rows = sorted(rows, key=lambda row: (str(row.get("map_name", "")), str(row.get("name_zh", "") or row.get("name_en", ""))))
        elif category == "resource":
            rows = sorted(rows, key=lambda row: (str(row.get("resource_name", "")), str(row.get("map_name", ""))))
        else:
            rows = sorted(rows, key=lambda row: str(row.get("name_zh", "") or row.get("name_en", "") or row.get("resource_name", "")))

        normalized_keyword = _normalize(keyword)
        if not normalized_keyword:
            return rows

        filtered = []
        for row in rows:
            haystack = [
                row.get("name_zh", ""),
                row.get("name_en", ""),
                row.get("resource_name", ""),
                row.get("map_name", ""),
                row.get("crate_id", ""),
                *row.get("aliases", []),
            ]
            if any(normalized_keyword in _normalize(str(value)) for value in haystack if str(value).strip()):
                filtered.append(row)
        return filtered

    def _list_label_for_row(self, category: str, row: dict[str, Any]) -> str:
        if category == "creature":
            return f"{row.get('name_zh') or row.get('name_en')} / {row.get('name_en', '')}"
        if category == "item":
            return f"{row.get('name_zh') or row.get('name_en')} / {row.get('name_en', '')}"
        if category == "resource":
            return f"{row.get('resource_name')} - {row.get('map_name')}"
        if category == "map":
            return f"{row.get('name_zh')} / {row.get('name_en')} ({row.get('status', '未知')})"
        if category == "crate":
            return f"{row.get('map_name')} - {row.get('name_zh') or row.get('name_en')}"
        return str(row)

    def _handle_alias_add(self, raw_query: str) -> QueryResult:
        if not self.allow_runtime_alias_edit:
            return QueryResult("当前配置已禁用运行期别名写入。", found=False)

        if "=" not in raw_query:
            return QueryResult("用法：/ark alias add <分类> <目标> = <别名>", found=False)

        left, alias_text = raw_query.split("=", 1)
        alias_text = alias_text.strip()
        left_parts = left.strip().split(maxsplit=1)
        if len(left_parts) < 2:
            return QueryResult("用法：/ark alias add <分类> <目标> = <别名>", found=False)

        category = self._resolve_category(left_parts[0])
        target_query = left_parts[1].strip()
        if category is None:
            return QueryResult(f"未识别的别名分类：{left_parts[0]}", found=False)
        if not alias_text:
            return QueryResult("别名不能为空。", found=False)

        row = self._find_row_for_alias(category, target_query)
        if row is None:
            return QueryResult(f"没有找到要添加别名的目标：{target_query}", found=False)

        return self._add_alias_to_row(category, row, alias_text, target_query)

    def _add_alias_to_row(
        self,
        category: str,
        row: dict[str, Any],
        alias_text: str,
        target_query: str,
    ) -> QueryResult:
        storage_key = self._row_storage_key(category, row)
        alias_bucket = self.custom_aliases.setdefault(category, {})
        existing_aliases = alias_bucket.setdefault(storage_key, [])
        if any(_normalize(existing) == _normalize(alias_text) for existing in existing_aliases):
            return QueryResult(f"别名“{alias_text}”已经存在于 {target_query}。", found=False)

        existing_aliases.append(alias_text)
        self._apply_aliases_for_category(category, storage_key, [alias_text])
        self._rebuild_indexes()
        try:
            self._save_alias_store()
        except OSError as exc:
            existing_aliases.pop()
            if not existing_aliases:
                alias_bucket.pop(storage_key, None)
            self._remove_aliases_for_category(category, storage_key, [alias_text])
            self._rebuild_indexes()
            return QueryResult(f"添加别名失败，无法写入文件：{exc}", found=False)

        label = self._list_label_for_row(category, row)
        return QueryResult(f"已为 {label} 添加别名：{alias_text}")

    def _render_alias_list(self, category: str, row: dict[str, Any]) -> QueryResult:
        aliases = [str(alias).strip() for alias in row.get("aliases", []) if str(alias).strip()]
        label = self._list_label_for_row(category, row)
        return QueryResult(f"{label}\n别名：{_join(aliases, ', ')}")

    def _handle_alias_list(self, raw_query: str) -> QueryResult:
        parts = raw_query.split(maxsplit=1)
        if len(parts) < 2:
            return QueryResult("用法：/ark alias list <分类> <目标>", found=False)

        category = self._resolve_category(parts[0])
        target_query = parts[1].strip()
        if category is None:
            return QueryResult(f"未识别的别名分类：{parts[0]}", found=False)

        row = self._find_row_for_alias(category, target_query)
        if row is None:
            return QueryResult(f"没有找到目标：{target_query}", found=False)

        return self._render_alias_list(category, row)

    def _handle_alias_shorthand(self, raw_query: str) -> QueryResult:
        compact = raw_query.strip()
        if not compact:
            return QueryResult("用法：/别名 南方巨兽龙 南巨", found=False)

        direct_target = self._infer_alias_target(compact)
        if not isinstance(direct_target, QueryResult):
            category, row = direct_target
            return self._render_alias_list(category, row)

        parts = compact.rsplit(maxsplit=1)
        if len(parts) == 1:
            return QueryResult(f"没有找到“{parts[0].strip()}”对应的可加别名目标。", found=False)

        target_query = parts[0].strip()
        alias_text = parts[1].strip()
        inferred = self._infer_alias_target(target_query)
        if isinstance(inferred, QueryResult):
            return inferred
        category, row = inferred
        return self._add_alias_to_row(category, row, alias_text, target_query)

    def _infer_alias_target(self, target_query: str) -> tuple[str, dict[str, Any]] | QueryResult:
        if not target_query:
            return QueryResult("别名目标不能为空。", found=False)

        matches: list[tuple[str, dict[str, Any]]] = []
        search_order = ("creature", "item", "map", "resource", "crate")
        for category in search_order:
            row = self._find_row_for_alias(category, target_query)
            if row is not None:
                matches.append((category, row))

        if not matches:
            return QueryResult(f"没有找到“{target_query}”对应的可加别名目标。", found=False)

        unique_matches: list[tuple[str, dict[str, Any]]] = []
        seen: set[tuple[str, str]] = set()
        for category, row in matches:
            identity = (category, self._row_storage_key(category, row))
            if identity in seen:
                continue
            seen.add(identity)
            unique_matches.append((category, row))

        if len(unique_matches) == 1:
            return unique_matches[0]

        choices = [f"{category}: {self._list_label_for_row(category, row)}" for category, row in unique_matches[: self.max_suggestions]]
        return QueryResult(
            "这个目标命中了多个分类，请改用显式写法："
            f"/ark alias add <分类> <目标> = <别名>\n候选：{_join(choices, ', ')}",
            found=False,
        )

    def _find_row_for_alias(self, category: str, target_query: str) -> dict[str, Any] | None:
        if category == "creature":
            return self._find_one(target_query, self.creature_index, allow_fuzzy=False)
        if category == "item":
            return self._find_one(target_query, self.item_index, allow_fuzzy=False)
        if category == "map":
            return self._find_one(target_query, self.map_index, allow_fuzzy=False)
        if category == "resource":
            keys = self._match_keys(target_query, self.resource_index, allow_fuzzy=False)
            rows = self.resource_index.get(keys[0], []) if keys else []
            return rows[0] if rows else None
        if category == "crate":
            keys = self._match_keys(target_query, self.crate_index, allow_fuzzy=False)
            rows = self.crate_index.get(keys[0], []) if keys else []
            return rows[0] if rows else None
        return None

    def query_map_info(self, raw_query: str) -> QueryResult:
        map_row = self._find_one(raw_query, self.map_index)
        if not map_row:
            return self._not_found("地图", raw_query, self.map_index, self.map_display)

        lines = [
            f"地图：{map_row['name_zh']} / {map_row['name_en']}",
            f"状态：{map_row['status']}",
            f"类型：{map_row['map_type']}",
            f"发布时间：{map_row['release_date']}",
            f"备注：{map_row['notes']}",
        ]
        self._append_source(lines, map_row)
        return QueryResult("\n".join(lines))

    def query_crate(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark crate 地图名 宝箱名", found=False)

        parsed = self._split_map_query(raw_query)
        crate_candidates: list[dict[str, Any]]
        if parsed is None:
            crate_candidates = self._find_crates(raw_query)
        else:
            map_name, crate_name = parsed
            crate_candidates = self._find_crates(crate_name, canonical_map=map_name)

        if not crate_candidates:
            return self._not_found("宝箱", raw_query, self.crate_index, self.crate_display)

        if len(crate_candidates) > 1:
            choices = [f"{row['map_name']} - {row['name_zh']}" for row in crate_candidates[: self.max_suggestions]]
            return QueryResult(
                f"找到了多个宝箱，请说得更具体一些：{_join(choices, ', ')}",
                found=False,
            )

        crate = crate_candidates[0]
        crate_items = self.loot_items_by_crate.get(crate["crate_id"], [])
        item_lines = []
        for entry in crate_items[: self.max_crate_items_display]:
            name = entry.get("item_name_zh") or entry.get("item_name_en") or "未知物品"
            parts = [name]
            if entry.get("quality"):
                parts.append(entry["quality"])
            if entry.get("quantity"):
                parts.append(f"x{entry['quantity']}")
            item_lines.append(" / ".join(parts))

        lines = [
            f"宝箱：{crate['map_name']} - {crate['name_zh']}",
            f"等级/类型：{crate['tier']}",
            f"颜色：{crate['color']}",
            f"位置：{_join(crate.get('locations', []))}",
            f"刷新说明：{crate['respawn']}",
            f"可开出示例：{_join(item_lines)}",
            f"备注：{crate['notes']}",
        ]
        if len(crate_items) > self.max_crate_items_display:
            lines.append(f"提示：当前只展示前 {self.max_crate_items_display} 条掉落示例。")
        self._append_source(lines, crate)
        return QueryResult("\n".join(lines))

    def query_loot(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark loot 物品名", found=False)

        item_source = self._find_one(raw_query, self.item_source_index)
        if not item_source:
            return self._not_found("宝箱掉落来源", raw_query, self.item_source_index, self.item_source_display)

        crate_lines = []
        for source in item_source.get("crate_sources", []):
            label = f"{source.get('map_name', '未知地图')} - {source.get('crate_name', '未知宝箱')}"
            details = []
            if source.get("quality"):
                details.append(source["quality"])
            if source.get("notes"):
                details.append(source["notes"])
            if details:
                label = f"{label}（{'；'.join(details)}）"
            crate_lines.append(label)

        lines = [
            f"掉落查询：{item_source['name_zh']} / {item_source['name_en']}",
            f"宝箱来源：{_join(crate_lines)}",
            f"制作来源：{_join(item_source.get('crafting', []))}",
            f"采集/击杀来源：{_join(item_source.get('harvest', []))}",
            f"备注：{item_source['notes']}",
        ]
        self._append_source(lines, item_source)
        return QueryResult("\n".join(lines))

    def query_source(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark source 物品名", found=False)

        item_source = self._find_one(raw_query, self.item_source_index)
        item = self._find_one(raw_query, self.item_index)
        if not item_source and not item:
            merged_index = self.item_source_index | self.item_index
            merged_display = self.item_source_display | self.item_display
            return self._not_found("来源", raw_query, merged_index, merged_display)

        lines = []
        display_name = (
            item_source.get("name_zh")
            if item_source
            else item.get("name_zh")
        )
        display_en = (
            item_source.get("name_en")
            if item_source
            else item.get("name_en")
        )
        lines.append(f"统一来源：{display_name} / {display_en}")

        if item:
            lines.append(f"主要获取：{_join(item.get('obtain_methods', []))}")
            lines.append(f"采集来源：{_join(item.get('harvest_from', []))}")
            lines.append(f"推荐工具：{_join(item.get('best_tools', []))}")

        if item_source:
            crate_lines = [f"{entry.get('map_name', '未知地图')} - {entry.get('crate_name', '未知宝箱')}" for entry in item_source.get("crate_sources", [])]
            lines.append(f"宝箱掉落：{_join(crate_lines)}")
            lines.append(f"制作链：{_join(item_source.get('crafting', []))}")
            lines.append(f"其他来源：{_join(item_source.get('harvest', []))}")
            lines.append(f"备注：{item_source['notes']}")
            self._append_source(lines, item_source)
        elif item:
            lines.append(f"备注：{item['notes']}")
            self._append_source(lines, item)

        return QueryResult("\n".join(lines))

    def smart_query(self, raw_query: str) -> QueryResult:
        raw_query = raw_query.strip()
        if not raw_query:
            return self.help_result()

        creature = self._find_one(raw_query, self.creature_index)
        if creature:
            return self.query_tame(raw_query)

        item_source = self._find_one(raw_query, self.item_source_index)
        if item_source:
            return self.query_source(raw_query)

        item = self._find_one(raw_query, self.item_index)
        if item:
            return self.query_item(raw_query)

        resource_rows = self._find_resource_rows(raw_query)
        if resource_rows:
            return self.query_resource(raw_query)

        map_row = self._find_one(raw_query, self.map_index)
        if map_row:
            return self.query_map_info(raw_query)

        crate_rows = self._find_crates(raw_query)
        if crate_rows:
            return self.query_crate(raw_query)

        return QueryResult(f"没识别出你的查询“{raw_query}”。可以试试：/ark help", found=False)

    def _find_one(
        self,
        raw_query: str,
        index: dict[str, dict[str, Any]],
        allow_fuzzy: bool = True,
    ) -> dict[str, Any] | None:
        keys = self._match_keys(raw_query, index, allow_fuzzy=allow_fuzzy)
        if not keys:
            return None
        return index[keys[0]]

    def _find_resource_rows(self, raw_query: str, canonical_map: str | None = None) -> list[dict[str, Any]]:
        keys = self._match_keys(raw_query, self.resource_index)
        rows = self.resource_index.get(keys[0], []) if keys else []
        if canonical_map is None:
            return rows
        return [row for row in rows if row["map_name"] == canonical_map]

    def _find_crates(self, raw_query: str, canonical_map: str | None = None) -> list[dict[str, Any]]:
        keys = self._match_keys(raw_query, self.crate_index)
        rows = self.crate_index.get(keys[0], []) if keys else []
        if canonical_map is None:
            return rows
        return [row for row in rows if row["map_name"] == canonical_map]

    def _split_map_query(self, raw_query: str) -> tuple[str, str] | None:
        parts = raw_query.split()
        if len(parts) < 2:
            return None

        map_row = self._find_one(parts[0], self.map_index)
        if not map_row:
            return None

        resource_part = " ".join(parts[1:])
        return str(map_row["name_zh"]), resource_part

    def _match_keys(self, raw_query: str, index: dict[str, Any], allow_fuzzy: bool = True) -> list[str]:
        key = _normalize(raw_query)
        if not key:
            return []

        if key in index:
            return [key]

        partial = [alias for alias in index if alias.startswith(key)]
        if partial:
            return partial[: self.max_suggestions]

        if not allow_fuzzy:
            return []

        cutoff = self.fuzzy_cjk_cutoff if _contains_cjk(key) else self.fuzzy_latin_cutoff
        return get_close_matches(key, list(index.keys()), n=self.max_suggestions, cutoff=cutoff)

    def _suggest_labels(
        self,
        raw_query: str,
        index: dict[str, Any],
        display_map: dict[str, str],
    ) -> list[str]:
        readable: list[str] = []
        for match in self._match_keys(raw_query, index):
            label = display_map.get(match, match)
            if label not in readable:
                readable.append(label)
        return readable[: self.max_suggestions]

    def _not_found(
        self,
        label: str,
        raw_query: str,
        index: dict[str, Any],
        display_map: dict[str, str],
    ) -> QueryResult:
        suggestions = self._suggest_labels(raw_query, index, display_map)
        return self._not_found_text(label, raw_query, suggestions)

    def _not_found_text(self, label: str, raw_query: str, suggestions: list[str]) -> QueryResult:
        if suggestions:
            return QueryResult(
                f"没有找到“{raw_query}”对应的{label}资料。你可以试试这些关键词：{', '.join(suggestions)}",
                found=False,
            )
        return QueryResult(f"没有找到“{raw_query}”对应的{label}资料。", found=False)

    def _append_source(self, lines: list[str], row: dict[str, Any]) -> None:
        if self.show_source_url and row.get("source_url"):
            lines.append(f"来源：{row['source_url']}")
