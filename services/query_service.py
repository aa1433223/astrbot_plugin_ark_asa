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


class ArkQueryService:
    def __init__(self, plugin_dir: Path, max_suggestions: int = 3, show_source_url: bool = True):
        self.plugin_dir = plugin_dir
        self.max_suggestions = max(1, max_suggestions)
        self.show_source_url = show_source_url

        self.creatures = self._load_json("creatures.json")
        self.items = self._load_json("items.json")
        self.resources = self._load_json("resources.json")
        self.map_aliases = self._load_json("map_aliases.json")

        self.creature_index = self._build_index(self.creatures)
        self.item_index = self._build_index(self.items)
        self.creature_display = self._build_display_map(self.creatures)
        self.item_display = self._build_display_map(self.items)
        self.resource_name_index = self._build_resource_index()
        self.resource_display = self._build_resource_display_map()
        self.map_name_index = self._build_map_alias_index()
        self.map_display = {key: value for key, value in self.map_name_index.items()}

    def _load_json(self, filename: str) -> list[dict[str, Any]] | dict[str, list[str]]:
        path = self.plugin_dir / "data" / filename
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _build_index(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for row in rows:
            names = [row.get("name_zh", ""), row.get("name_en", "")]
            names.extend(row.get("aliases", []))
            for name in names:
                key = _normalize(str(name))
                if key:
                    index[key] = row
        return index

    def _build_resource_index(self) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = {}
        for row in self.resources:
            aliases = [row.get("resource_name", "")]
            aliases.extend(row.get("aliases", []))
            for alias in aliases:
                key = _normalize(str(alias))
                if not key:
                    continue
                index.setdefault(key, []).append(row)
        return index

    def _build_map_alias_index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        for canonical, aliases in self.map_aliases.items():
            all_names = [canonical]
            all_names.extend(aliases)
            for name in all_names:
                key = _normalize(str(name))
                if key:
                    index[key] = canonical
        return index

    def _build_display_map(self, rows: list[dict[str, Any]]) -> dict[str, str]:
        display: dict[str, str] = {}
        for row in rows:
            label = row.get("name_zh") or row.get("name_en") or "未知条目"
            aliases = [row.get("name_zh", ""), row.get("name_en", "")]
            aliases.extend(row.get("aliases", []))
            for alias in aliases:
                key = _normalize(str(alias))
                if key:
                    display[key] = str(label)
        return display

    def _build_resource_display_map(self) -> dict[str, str]:
        display: dict[str, str] = {}
        for row in self.resources:
            label = str(row.get("resource_name", "未知资源"))
            aliases = [row.get("resource_name", "")]
            aliases.extend(row.get("aliases", []))
            for alias in aliases:
                key = _normalize(str(alias))
                if key:
                    display[key] = label
        return display

    def help_text(self) -> str:
        return self.help_result().message

    def help_result(self) -> QueryResult:
        return QueryResult(
            "\n".join(
                [
                    "ARK 生存飞升查询插件",
                    "",
                    "可用指令：",
                    "/ark help",
                    "/ark tame 南方巨兽龙",
                    "/ark code 霸王龙",
                    "/ark item 水泥浆",
                    "/ark resource 金属",
                    "/ark map 孤岛 水晶",
                    "",
                    "快捷指令：",
                    "/驯龙 霸王龙",
                    "/代码 聚合物",
                    "/材料 黑珍珠",
                    "/资源 黑曜石",
                    "/地图 仙境 金属",
                    "",
                    "说明：",
                    "1. 首版为本地资料库，查询速度快，方便后续继续补数据。",
                    "2. 名称支持简称、英文名和常见别名模糊匹配。",
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
            f"刷新地图：{', '.join(creature['maps'])}",
            f"备注：{creature['notes']}",
            f"控制台：admincheat summon {creature['blueprint_path']}",
            f"高等级：admincheat gmsummon \"{creature['blueprint_path']}\" 150",
        ]
        self._append_source(lines, creature)
        return QueryResult("\n".join(lines))

    def query_code(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark code 生物名 或 /ark code 物品名", found=False)

        creature = self._find_one(raw_query, self.creature_index)
        if creature:
            lines = [
                f"生物代码：{creature['name_zh']} / {creature['name_en']}",
                f"召唤：admincheat summon {creature['blueprint_path']}",
                f"高等级召唤：admincheat gmsummon \"{creature['blueprint_path']}\" 150",
                f"蓝图路径：{creature['full_blueprint']}",
            ]
            self._append_source(lines, creature)
            return QueryResult("\n".join(lines))

        item = self._find_one(raw_query, self.item_index)
        if item:
            lines = [
                f"物品代码：{item['name_zh']} / {item['name_en']}",
                f"给予物品：admincheat giveitemnum {item['item_code']} 1 0 0",
                f"蓝图路径：{item['blueprint_path']}",
            ]
            self._append_source(lines, item)
            return QueryResult("\n".join(lines))

        merged_index = self.creature_index | self.item_index
        merged_display = self.creature_display | self.item_display
        suggestions = self._collect_suggestions(raw_query, merged_index, merged_display)
        return self._not_found_text("代码", raw_query, suggestions)

    def query_item(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark item 材料名", found=False)

        item = self._find_one(raw_query, self.item_index)
        if not item:
            return self._not_found("材料", raw_query, self.item_index, self.item_display)

        lines = [
            f"材料：{item['name_zh']} / {item['name_en']}",
            f"主要获取：{'; '.join(item['obtain_methods'])}",
            f"掉落或采集来源：{'; '.join(item['harvest_from'])}",
            f"推荐工具：{'; '.join(item['best_tools'])}",
            f"控制台：admincheat giveitemnum {item['item_code']} 1 0 0",
            f"备注：{item['notes']}",
        ]
        self._append_source(lines, item)
        return QueryResult("\n".join(lines))

    def query_resource(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark resource 资源名", found=False)

        rows = self._find_resource_rows(raw_query)
        if not rows:
            return self._not_found("资源", raw_query, self.resource_name_index, self.resource_display)

        lines = [f"资源：{rows[0]['resource_name']}"]
        for row in rows:
            lines.append(f"{row['map_name']}：{'; '.join(row['areas'])}")
        lines.append("提示：如需更精确位置，请用 /ark map 地图名 资源名")
        self._append_source(lines, rows[0])
        return QueryResult("\n".join(lines))

    def query_map_resource(self, raw_query: str) -> QueryResult:
        if not raw_query:
            return QueryResult("用法：/ark map 地图名 资源名", found=False)

        parsed = self._split_map_query(raw_query)
        if parsed is None:
            return QueryResult("格式示例：/ark map 孤岛 金属", found=False)

        map_name, resource_name = parsed
        rows = self._find_resource_rows(resource_name, canonical_map=map_name)
        if not rows:
            return QueryResult(
                f"没有找到“{map_name}”中的“{resource_name}”资料。你可以先试试：/ark resource {resource_name}",
                found=False,
            )

        row = rows[0]
        lines = [
            f"地图资源：{row['map_name']} - {row['resource_name']}",
            f"推荐区域：{'; '.join(row['areas'])}",
            f"坐标参考：{'; '.join(row['coordinates'])}",
            f"风险提示：{row['risk_level']}",
            f"备注：{row['notes']}",
        ]
        self._append_source(lines, row)
        return QueryResult("\n".join(lines))

    def smart_query(self, raw_query: str) -> QueryResult:
        raw_query = raw_query.strip()
        if not raw_query:
            return self.help_result()

        creature = self._find_one(raw_query, self.creature_index)
        if creature:
            return self.query_tame(raw_query)

        item = self._find_one(raw_query, self.item_index)
        if item:
            return self.query_item(raw_query)

        resource_rows = self._find_resource_rows(raw_query)
        if resource_rows:
            return self.query_resource(raw_query)

        return QueryResult(
            f"没识别出你的查询“{raw_query}”。可以试试：/ark help",
            found=False,
        )

    def _find_one(self, raw_query: str, index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
        key = _normalize(raw_query)
        if key in index:
            return index[key]

        for alias, row in index.items():
            if key and (key in alias or alias in key):
                return row

        suggestions = self._collect_suggestions(raw_query, index)
        if suggestions:
            return index[suggestions[0]]
        return None

    def _find_resource_rows(self, raw_query: str, canonical_map: str | None = None) -> list[dict[str, Any]]:
        key = _normalize(raw_query)
        rows = self.resource_name_index.get(key, [])
        if not rows:
            for alias, candidate_rows in self.resource_name_index.items():
                if key and (key in alias or alias in key):
                    rows = candidate_rows
                    break
        if not rows:
            suggestions = self._collect_suggestions(raw_query, self.resource_name_index)
            if suggestions:
                suggestion_key = _normalize(suggestions[0])
                rows = self.resource_name_index.get(suggestion_key, [])

        if canonical_map is None:
            return rows

        return [row for row in rows if row["map_name"] == canonical_map]

    def _split_map_query(self, raw_query: str) -> tuple[str, str] | None:
        parts = raw_query.split()
        if len(parts) < 2:
            return None

        map_part = parts[0]
        resource_part = " ".join(parts[1:])
        canonical_map = self.map_name_index.get(_normalize(map_part))
        if not canonical_map:
            suggestions = self._collect_suggestions(map_part, self.map_name_index, self.map_display)
            if not suggestions:
                return None
            canonical_map = self.map_name_index[_normalize(suggestions[0])]
        return canonical_map, resource_part

    def _collect_suggestions(
        self,
        raw_query: str,
        index: dict[str, Any],
        display_map: dict[str, str] | None = None,
    ) -> list[str]:
        key = _normalize(raw_query)
        if not key:
            return []

        matches = get_close_matches(key, list(index.keys()), n=self.max_suggestions, cutoff=0.45)
        if not matches:
            matches = [alias for alias in index if key in alias or alias in key][: self.max_suggestions]

        if not display_map:
            return matches[: self.max_suggestions]

        readable: list[str] = []
        for match in matches:
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
        suggestions = self._collect_suggestions(raw_query, index, display_map)
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
