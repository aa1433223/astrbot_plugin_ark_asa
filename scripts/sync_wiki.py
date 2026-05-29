from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from opencc import OpenCC
except Exception:
    OpenCC = None


API_URL = "https://ark.wiki.gg/api.php"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROFILE_PATH = SCRIPT_DIR / "sync_profiles.json"
DEFAULT_USER_AGENT = "astrbot-plugin-ark-asa-sync/0.3 (+https://github.com/aa1433223/astrbot_plugin_ark_asa)"
SIMPLIFIED_CONVERTER = OpenCC("t2s") if OpenCC else None
ENGLISH_BASE_ALIASES = {
    "trex": "Rex",
    "mosasaur": "Mosasaurus",
    "spinosaurus": "Spino",
}
MANUAL_CREATURE_ZH = {
    "Abominable Snowman": "雪怪",
    "Amargasaurus": "阿玛加龙",
    "Andrewsarchus": "安氏中兽",
    "Archelon": "古巨龟",
    "Armadoggo": "犰狳狗",
    "Astrocetus": "星鲸",
    "Astrodelphis": "星海豚",
    "Attack Drone": "攻击无人机",
    "Aureliax": "奥瑞利亚克斯",
    "Beyla": "贝拉",
    "Beyla Spawn": "贝拉召唤物",
    "Bison": "野牛",
    "Bloodstalker": "血蛛",
    "Boaratos": "博阿拉托斯",
    "Bronto": "雷龙",
    "Burrowbuck": "掘穴鹿",
    "Carcharodontosaurus": "鲨齿龙",
    "Cat": "猫",
    "Cat (Feline Form Skill)": "猫（猫形态技能）",
    "Ceratosaurus": "角鼻龙",
    "Cerberax": "刻耳柏拉克斯",
    "Chrysaora": "海刺水母",
    "Cosmo": "科斯莫",
    "Corrupted Avatar": "腐化化身",
    "Corrupted Master Controller": "腐化主控者",
    "Corrupted Survivor": "腐化幸存者",
    "Cryolophosaurus": "冰脊龙",
    "Cymathoa": "锡马托亚",
    "Dakosaurus": "达科龙",
    "Defense Unit": "防御单元",
    "Deinonychus": "恐爪龙",
    "Deinosuchus": "帝鳄",
    "Deinotherium": "恐象",
    "Desmodus": "吸血蝠",
    "Desert Titan Flock": "沙漠泰坦群",
    "Dinopithecus": "恐猿",
    "Dinopithecus King": "恐猿之王",
    "Dire Polar Bear": "凶暴北极熊",
    "Drakeling": "幼龙",
    "Dreadmare": "惧魇马",
    "Dreadnoughtus": "无畏龙",
    "Eel Minion": "鳗鱼仆从",
    "Elderclaw": "长老爪",
    "Enforcer": "执法者",
    "Enigmasaur": "谜龙",
    "Erymanthian & Kalydonios": "厄律曼托斯与卡吕多尼俄斯",
    "Exo-Mek": "外骨骼机甲",
    "Experimental Giganotosaurus": "实验体南方巨兽龙",
    "Fasolasuchus": "法索拉鳄",
    "Fenrir": "芬里尔",
    "Fenrisúlfr": "芬里斯狼",
    "Ferox": "费洛克斯",
    "Fjordhawk": "峡湾鹰",
    "Flovis": "弗洛维斯",
    "Fractalis": "弗拉克塔利斯",
    "GachaClaus": "圣诞嘎查",
    "Giant Queen Bee": "巨型蜂后",
    "Giant Worker Bee": "巨型工蜂",
    "Gigadesmodus": "巨型吸血蝠",
    "Gigantoraptor": "巨盗龙",
    "Gloon": "格隆",
    "Grand Tortugar": "巨型托图加",
    "Grendel": "格伦德尔",
    "Hati and Sköll": "哈提与斯库尔",
    "Helper Wisp (Wisp of Industry Skill)": "助手微光（工业微光技能）",
    "Helicoprion": "螺旋齿鲨",
    "Homarus": "龙虾",
    "Hover Skiff": "悬浮艇",
    "Hulking Revenant": "巨躯亡魂",
    "Human": "人类",
    "Hydraskos": "海德拉斯科斯",
    "Iceworm Male": "公冰虫",
    "Iceworm Queen": "冰虫女王",
    "Insect Swarm": "虫群",
    "Istiophorus": "旗鱼",
    "Jerboa Elf": "精灵跳鼠",
    "Kathreptis": "卡斯雷普提斯",
    "Kirayli": "基拉伊利",
    "Lava Elemental": "熔岩元素",
    "Lightning Infused Rex": "闪电灌注霸王龙",
    "Love Bird": "爱心鸟",
    "Love Bug": "爱心虫",
    "Macro-Summoner": "巨型召唤师",
    "Macrophage": "巨噬体",
    "Maeguana": "梅瓜纳",
    "Maewing": "护幼兽",
    "Magmasaur": "岩浆龙",
    "Malleocephalus": "马勒头龙",
    "Malwyn": "马尔温",
    "Mantis Shrimp": "虾蛄",
    "Mega Mek": "巨型机甲",
    "Megachelon": "巨龟",
    "Megalodon": "巨齿鲨",
    "Megaraptor": "巨盗龙",
    "Mek": "机甲",
    "Mek Knight": "机甲骑士",
    "Minotarchos": "米诺塔科斯",
    "Minotaur": "牛头怪",
    "Moeder, Master of the Ocean": "海洋主宰莫德尔",
    "Monodon": "独角鲸",
    "Mouser": "捕鼠兽",
    "Mudpuppy": "泥狗龙",
    "Natrix": "纳特里克斯",
    "Neophyte": "新徒",
    "Noglin": "寄脑魔",
    "Nunatak": "努纳塔克",
    "Oasisaur": "绿洲龙",
    "Ocepechelon": "奥赛佩凯龙",
    "Onchopristis": "锯鳐",
    "Ossidon": "奥西登",
    "Palaeoctopus": "古章鱼",
    "Parakeet Fish School": "鹦嘴鱼群",
    "Party Dodo": "派对渡渡鸟",
    "Pegomastax Grouch": "暴躁似鸡龙",
    "Piercer": "穿刺者",
    "Polar Bear": "北极熊",
    "Pulmonoscorpius Monarch": "肺蝎君主",
    "Pygocentrus": "食人鱼",
    "Pyromane": "炎鬃",
    "Qarmoutus": "卡尔穆图斯",
    "Rare X-Sabertooth Salmon": "稀有X-剑齿鲑鱼",
    "Reindeer": "驯鹿",
    "Rhyniognatha": "莱尼虫",
    "Rhyniognatha Drone": "莱尼虫工蜂",
    "Riftcrawler": "裂隙爬行者",
    "Riftwalker": "裂隙行者",
    "Rubble Bear": "碎岩熊",
    "Santa's Big Helper": "圣诞老人的大帮手",
    "Scout": "侦察者",
    "Salmon": "鲑鱼",
    "Scrap Golem": "废料魔像",
    "Seahorse": "海马",
    "Shadowmane": "影鬃",
    "Shastasaurus": "萨斯特鱼龙",
    "Sinomacrops": "中国大翼兽",
    "Sir-5rM8": "西尔-5rM8",
    "Snarer": "诱捕者",
    "Skeleton": "骷髅",
    "Stego": "剑龙",
    "Solwyn": "索尔温",
    "Spirit Direwolf (Spirit Beasts Skill)": "灵魂恐狼（灵兽技能）",
    "Steinbjörn": "斯坦比约恩",
    "Stereolepis": "巨鲈",
    "Summoner": "召唤师",
    "Super Turkey": "超级火鸡",
    "Takifugu": "河豚",
    "Tek Stryder": "泰克机甲牛",
    "Thanatos": "塔纳托斯",
    "Thodes": "索德斯",
    "Thunnus": "金枪鱼",
    "Tidepup": "潮汐幼崽",
    "Tiktaalik": "提塔利克鱼",
    "Trike": "三角龙",
    "Tridacna": "砗磲",
    "Tropeognathus": "喙嘴翼龙",
    "Unicorn": "独角兽",
    "Valentines Coelacanth": "情人节腔棘鱼",
    "Veilwyn": "维尔温",
    "Voidwyrm": "虚空飞龙",
    "Vulcanite": "武尔卡耐特",
    "Vulcanithys": "武尔卡尼西斯",
    "Warden": "守卫者",
    "Xiphactinus": "剑射鱼",
    "Yeti": "雪怪",
    "Yi Ling": "翼灵",
    "Zomdodo": "僵尸渡渡鸟",
}


class WikiClient:
    def __init__(
        self,
        api_url: str = API_URL,
        timeout: int = 30,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
    ):
        self.api_url = api_url
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_retries = max_retries

    def request(self, params: dict[str, Any]) -> dict[str, Any]:
        query = dict(params)
        query.setdefault("format", "json")
        query.setdefault("formatversion", 2)
        url = f"{self.api_url}?{urllib.parse.urlencode(query, doseq=True)}"

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                    "Connection": "close",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(2 * attempt, 5))

        if last_error:
            raise last_error
        raise RuntimeError("request failed without a captured exception")

    def cargo_tables(self) -> dict[str, Any]:
        return self.request({"action": "cargotables"})

    def cargo_fields(self, table: str) -> dict[str, Any]:
        return self.request({"action": "cargofields", "table": table})

    def cargo_query(
        self,
        table: str,
        fields: str,
        where: str = "",
        join_on: str = "",
        group_by: str = "",
        order_by: str = "",
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        offset = 0
        rows: list[dict[str, Any]] = []

        while True:
            params = {
                "action": "cargoquery",
                "tables": table,
                "fields": fields,
                "limit": str(limit),
                "offset": str(offset),
            }
            if where:
                params["where"] = where
            if join_on:
                params["join_on"] = join_on
            if group_by:
                params["group_by"] = group_by
            if order_by:
                params["order_by"] = order_by

            payload = self.request(params)
            batch = payload.get("cargoquery", [])
            if not batch:
                break

            for item in batch:
                title = item.get("title", {})
                if isinstance(title, dict):
                    rows.append(title)
                else:
                    rows.append(item)

            if len(batch) < limit:
                break
            offset += limit

        return rows

    def parse_page(self, page: str, uselang: str = "") -> dict[str, Any]:
        params: dict[str, Any] = {"action": "parse", "page": page, "prop": "text"}
        if uselang:
            params["uselang"] = uselang
        return self.request(params)

    def langlinks(self, titles: list[str], target_lang: str = "zh") -> dict[str, Any]:
        return self.request(
            {
                "action": "query",
                "prop": "langlinks",
                "titles": "|".join(titles),
                "lllang": target_lang,
                "lllimit": "max",
            }
        )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_profiles(path: Path = DEFAULT_PROFILE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def filter_candidate_tables(payload: dict[str, Any], keywords: list[str]) -> list[dict[str, Any]]:
    tables = payload.get("cargotables", [])
    lowered_keywords = [keyword.lower() for keyword in keywords]
    result = []
    for row in tables:
        if isinstance(row, dict):
            table = str(row.get("table", ""))
            entry = row
        else:
            table = str(row)
            entry = {"table": table}
        if any(keyword in table.lower() for keyword in lowered_keywords):
            result.append(entry)
    return result


def extract_wiki_links_from_parse_payload(payload: dict[str, Any], contains: str = "") -> list[str]:
    html_text = payload.get("parse", {}).get("text", "")
    if isinstance(html_text, dict):
        html_text = html_text.get("*", "")

    matches = re.findall(r'href="/wiki/([^"#?]+)', str(html_text))
    links: list[str] = []
    for match in matches:
        page = html.unescape(match).replace("_", " ")
        if contains and contains.lower() not in page.lower():
            continue
        if page not in links:
            links.append(page)
    return links


def extract_loot_subpages(master_input: Path, output_file: Path) -> list[str]:
    payload = json.loads(master_input.read_text(encoding="utf-8"))
    links = extract_wiki_links_from_parse_payload(payload, contains="Loot tables/")
    result = [link for link in links if link.startswith("Loot tables/")]
    write_json(output_file, result)
    return result


def probe_asa(client: WikiClient, output_dir: Path, profile_path: Path) -> dict[str, Any]:
    profiles = load_profiles(profile_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    tables_payload = client.cargo_tables()
    write_json(output_dir / "cargo_tables.json", tables_payload)

    candidate_tables = filter_candidate_tables(
        tables_payload,
        profiles.get("candidate_table_keywords", []),
    )
    write_json(output_dir / "cargo_candidate_tables.json", candidate_tables)

    fields_snapshot: dict[str, Any] = {}
    for row in candidate_tables:
        table_name = row.get("table")
        if not table_name:
            continue
        try:
            fields_snapshot[str(table_name)] = client.cargo_fields(str(table_name))
        except Exception as exc:
            fields_snapshot[str(table_name)] = {"error": str(exc)}
    write_json(output_dir / "cargo_candidate_fields.json", fields_snapshot)

    page_snapshot: dict[str, Any] = {}
    page_links: dict[str, list[str]] = {}
    for section, pages in profiles.get("known_pages", {}).items():
        page_snapshot[section] = {}
        page_links[section] = []
        for page in pages:
            try:
                payload = client.parse_page(page)
                page_snapshot[section][page] = payload
                page_links[section].extend(extract_wiki_links_from_parse_payload(payload))
            except Exception as exc:
                page_snapshot[section][page] = {"error": str(exc)}
        page_links[section] = _dedupe_list(page_links[section])

    write_json(output_dir / "page_probe.json", page_snapshot)
    write_json(output_dir / "page_links.json", page_links)

    manifest = {
        "profile_path": str(profile_path),
        "candidate_table_count": len(candidate_tables),
        "candidate_tables": [row.get("table") for row in candidate_tables],
        "known_page_sections": list(profiles.get("known_pages", {}).keys()),
        "generated_files": [
            "cargo_tables.json",
            "cargo_candidate_tables.json",
            "cargo_candidate_fields.json",
            "page_probe.json",
            "page_links.json",
        ],
    }
    write_json(output_dir / "probe_manifest.json", manifest)
    return manifest


def rebuild_item_sources(data_dir: Path, output_file: Path) -> list[dict[str, Any]]:
    loot_crates = json.loads((data_dir / "loot_crates.json").read_text(encoding="utf-8"))
    loot_items = json.loads((data_dir / "loot_crate_items.json").read_text(encoding="utf-8"))

    crate_lookup = {row["crate_id"]: row for row in loot_crates}
    grouped: dict[str, dict[str, Any]] = {}

    for row in loot_items:
        item_name_zh = row.get("item_name_zh", "")
        item_name_en = row.get("item_name_en", "")
        key = item_name_zh or item_name_en
        if not key:
            continue

        source = grouped.setdefault(
            key,
            {
                "name_zh": item_name_zh,
                "name_en": item_name_en,
                "aliases": [],
                "crafting": [],
                "harvest": [],
                "crate_sources": [],
                "notes": "由 loot_crate_items.json 自动生成的反向索引。",
                "source_url": row.get("source_url", ""),
            },
        )

        crate = crate_lookup.get(row["crate_id"], {})
        source["crate_sources"].append(
            {
                "map_name": crate.get("map_name", ""),
                "crate_name": crate.get("name_zh", ""),
                "quality": row.get("quality", ""),
                "notes": row.get("notes", ""),
            }
        )

    result = list(grouped.values())
    write_json(output_file, result)
    return result


def fetch_langlinks_for_titles(
    client: WikiClient,
    titles: list[str],
    target_lang: str,
    batch_size: int = 20,
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for start in range(0, len(titles), batch_size):
        batch = titles[start : start + batch_size]
        payload = client.langlinks(batch, target_lang=target_lang)
        pages = payload.get("query", {}).get("pages", [])
        for page in pages:
            title = str(page.get("title", "")).strip()
            translated = ""
            for link in page.get("langlinks", []):
                if link.get("lang") == target_lang:
                    translated = str(link.get("*") or link.get("title") or "").strip()
                    break
            if title:
                mapping[title] = translated
    return mapping


def extract_dossiers_creature_map(
    dossiers_input: Path,
    creatures_input: Path,
    output_file: Path,
) -> dict[str, dict[str, str]]:
    creatures = json.loads(creatures_input.read_text(encoding="utf-8"))
    valid_names = {
        str(row.get("name_en", "")).strip()
        for row in creatures
        if str(row.get("name_en", "")).strip()
    }

    payload = json.loads(dossiers_input.read_text(encoding="utf-8"))
    text = payload.get("parse", {}).get("text", "")
    if isinstance(text, dict):
        text = text.get("*", "")

    matches = re.findall(r'<a[^>]+href="/wiki/([^"#?]+)"[^>]*>(.*?)</a>', str(text), re.I | re.S)
    mapping: dict[str, dict[str, str]] = {}
    for href, label in matches:
        clean_href = html.unescape(href).replace("_", " ").strip()
        clean_label = re.sub(r"<.*?>", "", label)
        clean_label = html.unescape(clean_label).strip()
        if clean_href not in valid_names:
            continue
        if not clean_label or clean_label == clean_href:
            continue
        mapping[clean_href] = {
            "traditional": clean_label,
            "simplified": _to_simplified(clean_label),
        }

    write_json(output_file, mapping)
    return mapping


def _parse_loot_payload(payload: dict[str, Any], page_name: str) -> list[dict[str, Any]]:
    text = payload.get("parse", {}).get("text", "")
    if isinstance(text, dict):
        text = text.get("*", "")

    page_label = page_name.replace("_", " ")
    page_parts = page_label.split("/")
    map_name = page_parts[1] if len(page_parts) > 1 else "Unknown Map"
    loot_section = page_parts[2] if len(page_parts) > 2 else "Unknown Section"

    pattern = re.compile(
        r"<dl><dt>\s*([^<]+?)\s*</dt></dl>\s*<div class=\"tabber.*?<article class=\"tabber__panel\"[^>]*id=\"Overview-\d+\".*?<ul[^>]*class=\"itemlist\"[^>]*>(.*?)</ul>",
        re.I | re.S,
    )
    rows: list[dict[str, Any]] = []
    for heading_html, items_html in pattern.findall(text):
        heading = re.sub(r"<.*?>", "", heading_html)
        heading = html.unescape(heading).strip()
        if not heading:
            continue

        item_titles = re.findall(r'<a href="/wiki/[^"]+" title="([^"]+)">', items_html, re.I)
        item_names = _dedupe_list([html.unescape(item).strip() for item in item_titles if item.strip()])
        rows.append(
            {
                "page_name": page_label,
                "map_name": map_name,
                "loot_section": loot_section,
                "crate_name": heading,
                "crate_id": _safe_filename(f"{map_name}_{loot_section}_{heading}").lower(),
                "items": item_names,
            }
        )

    return rows


def parse_loot_subpage(input_file: Path, page_name: str, output_file: Path) -> list[dict[str, Any]]:
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    rows = _parse_loot_payload(payload, page_name)

    write_json(output_file, rows)
    return rows


def build_loot_datasets(
    pages_json: Path,
    payload_dir: Path,
    crates_output: Path,
    items_output: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pages = json.loads(pages_json.read_text(encoding="utf-8"))
    crate_rows: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []

    for page_name in pages:
        payload_path = payload_dir / f"{_safe_filename(str(page_name))}.json"
        if not payload_path.exists():
            continue
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        parsed_rows = _parse_loot_payload(payload, str(page_name))
        for row in parsed_rows:
            crate_rows.append(
                {
                    "crate_id": row["crate_id"],
                    "map_name": row["map_name"],
                    "name_zh": row["crate_name"],
                    "name_en": row["crate_name"],
                    "aliases": [],
                    "tier": row["loot_section"],
                    "color": row["crate_name"],
                    "locations": [],
                    "respawn": "待补充",
                    "notes": f"来自 {row['page_name']}",
                    "source_url": f"https://ark.wiki.gg/wiki/{urllib.parse.quote(str(page_name).replace(' ', '_'))}",
                }
            )
            for item_name in row["items"]:
                item_rows.append(
                    {
                        "crate_id": row["crate_id"],
                        "item_name_zh": item_name,
                        "item_name_en": item_name,
                        "quality": "",
                        "quantity": "",
                        "notes": f"来自 {row['crate_name']}",
                        "source_url": f"https://ark.wiki.gg/wiki/{urllib.parse.quote(str(page_name).replace(' ', '_'))}",
                    }
                )

    crate_rows = _dedupe_dict_rows(crate_rows, ("crate_id",))
    item_rows = _dedupe_dict_rows(item_rows, ("crate_id", "item_name_en"))

    write_json(crates_output, crate_rows)
    write_json(items_output, item_rows)
    return crate_rows, item_rows


def build_creature_name_overrides(
    creatures_input: Path,
    langlinks_input: Path,
    manual_overrides_input: Path | None,
    output_file: Path,
) -> dict[str, Any]:
    creatures = json.loads(creatures_input.read_text(encoding="utf-8"))
    langlinks = json.loads(langlinks_input.read_text(encoding="utf-8"))
    manual_overrides = {}
    if manual_overrides_input and manual_overrides_input.exists():
        manual_overrides = json.loads(manual_overrides_input.read_text(encoding="utf-8"))

    overrides: dict[str, Any] = {}
    for row in creatures:
        name_en = str(row.get("name_en", "")).strip()
        if not name_en:
            continue

        manual = manual_overrides.get(name_en, {})
        zh_name = str(langlinks.get(name_en, "") or manual.get("name_zh", "")).strip()
        aliases = _dedupe_list([zh_name, *manual.get("aliases", [])] if zh_name else list(manual.get("aliases", [])))
        if zh_name or aliases:
            overrides[name_en] = {
                "name_zh": zh_name,
                "aliases": aliases,
            }

    write_json(output_file, overrides)
    return overrides


def build_creature_name_overrides_from_base_map(
    creatures_input: Path,
    base_map_input: Path,
    manual_overrides_input: Path | None,
    output_file: Path,
) -> dict[str, Any]:
    creatures = json.loads(creatures_input.read_text(encoding="utf-8"))
    base_map = json.loads(base_map_input.read_text(encoding="utf-8"))
    manual_overrides = {}
    if manual_overrides_input and manual_overrides_input.exists():
        manual_overrides = json.loads(manual_overrides_input.read_text(encoding="utf-8"))

    overrides: dict[str, Any] = {}
    base_name_map = _build_combined_base_name_map(base_map, manual_overrides)

    for row in creatures:
        name_en = str(row.get("name_en", "")).strip()
        if not name_en:
            continue

        manual = manual_overrides.get(name_en, {})
        zh_name = str(manual.get("name_zh", "")).strip()
        aliases = list(manual.get("aliases", []))

        if not zh_name and name_en in base_name_map:
            zh_name = base_name_map[name_en]

        if not zh_name:
            generated = _translate_variant_name(name_en, base_name_map)
            zh_name = generated.get("name_zh", "")
            aliases.extend(generated.get("aliases", []))

        if zh_name:
            aliases = _dedupe_list([zh_name, *aliases])
            overrides[name_en] = {
                "name_zh": zh_name,
                "aliases": aliases,
            }

    for name_en, manual in manual_overrides.items():
        if name_en not in overrides and (manual.get("name_zh") or manual.get("aliases")):
            overrides[name_en] = {
                "name_zh": str(manual.get("name_zh", "")).strip(),
                "aliases": _dedupe_list(list(manual.get("aliases", []))),
            }

    write_json(output_file, overrides)
    return overrides


def merge_creature_translations(
    creatures_input: Path,
    overrides_input: Path,
    output_file: Path,
) -> list[dict[str, Any]]:
    creatures = json.loads(creatures_input.read_text(encoding="utf-8"))
    overrides = json.loads(overrides_input.read_text(encoding="utf-8"))
    merged_rows: list[dict[str, Any]] = []

    for row in creatures:
        current = dict(row)
        name_en = str(current.get("name_en", "")).strip()
        override = overrides.get(name_en, {})
        zh_name = str(override.get("name_zh", "")).strip()
        aliases = _dedupe_list(list(current.get("aliases", [])) + list(override.get("aliases", [])))
        if zh_name:
            current["name_zh"] = zh_name
        current["aliases"] = aliases
        merged_rows.append(current)

    write_json(output_file, merged_rows)
    return merged_rows


def build_creature_translation_report(
    creatures_input: Path,
    translated_input: Path,
    output_file: Path,
    template_output: Path | None = None,
) -> dict[str, Any]:
    original_rows = json.loads(creatures_input.read_text(encoding="utf-8"))
    translated_rows = json.loads(translated_input.read_text(encoding="utf-8"))
    translated_map = {
        str(row.get("name_en", "")).strip(): row
        for row in translated_rows
        if str(row.get("name_en", "")).strip()
    }

    unresolved_plain: list[str] = []
    unresolved_variant: list[str] = []
    untranslated_names: list[str] = []
    prefix_counts: dict[str, int] = {}
    manual_template: dict[str, Any] = {}

    translated_count = 0
    for row in original_rows:
        name_en = str(row.get("name_en", "")).strip()
        if not name_en:
            continue
        translated_row = translated_map.get(name_en, row)
        name_zh = str(translated_row.get("name_zh", "")).strip()
        if name_zh and name_zh != name_en:
            translated_count += 1
            continue

        untranslated_names.append(name_en)
        first_token = name_en.split(" ", 1)[0] if " " in name_en else "(plain)"
        prefix_counts[first_token] = prefix_counts.get(first_token, 0) + 1
        if " " in name_en or "(" in name_en or "-" in name_en:
            unresolved_variant.append(name_en)
        else:
            unresolved_plain.append(name_en)
        manual_template[name_en] = {"name_zh": "", "aliases": []}

    total = len([row for row in original_rows if str(row.get("name_en", "")).strip()])
    report = {
        "total": total,
        "translated": translated_count,
        "untranslated": len(untranslated_names),
        "coverage_ratio": round((translated_count / total), 4) if total else 0,
        "untranslated_prefix_counts": dict(sorted(prefix_counts.items(), key=lambda item: (-item[1], item[0]))),
        "untranslated_names": untranslated_names,
        "unresolved_plain_names": unresolved_plain,
        "unresolved_variant_names": unresolved_variant,
    }

    write_json(output_file, report)
    if template_output:
        write_json(template_output, manual_template)
    return report


def autofill_creature_translations(
    creatures_input: Path,
    dossiers_input: Path,
    manual_overrides_input: Path | None,
    base_map_output: Path,
    overrides_output: Path,
    translated_output: Path,
    report_output: Path,
    template_output: Path | None = None,
) -> dict[str, Any]:
    base_map = extract_dossiers_creature_map(dossiers_input, creatures_input, base_map_output)
    build_creature_name_overrides_from_base_map(
        creatures_input,
        base_map_output,
        manual_overrides_input,
        overrides_output,
    )
    merge_creature_translations(creatures_input, overrides_output, translated_output)
    return build_creature_translation_report(
        creatures_input,
        translated_output,
        report_output,
        template_output=template_output,
    )


def build_creatures_dataset(input_file: Path, output_file: Path) -> list[dict[str, Any]]:
    rows = json.loads(input_file.read_text(encoding="utf-8"))
    result = []
    for row in rows:
        page = row.get("Page") or row.get("_pageName") or row.get("Name") or "Unknown Creature"
        result.append(
            {
                "name_zh": page,
                "name_en": row.get("Name", page),
                "aliases": [],
                "tame_type": "待补充",
                "tame_food": "待补充",
                "knockout": "待补充",
                "saddle": _build_saddle_text(row.get("Saddle"), row.get("SaddleLevel")),
                "maps": _split_list_like(row.get("WildMaps")),
                "notes": "；".join(
                    [
                        f"可驯服：{_to_bool_text(row.get('Tameable'))}",
                        f"可繁殖：{_to_bool_text(row.get('Breedable'))}",
                        f"可骑乘：{_to_bool_text(row.get('Rideable'))}",
                        f"食性：{row.get('Diet', '未知')}",
                        f"性情：{row.get('Temperament', '未知')}",
                    ]
                ),
                "blueprint_path": row.get("EntityId", ""),
                "full_blueprint": "",
                "source_url": f"https://ark.wiki.gg/wiki/{urllib.parse.quote(str(page).replace(' ', '_'))}",
            }
        )
    write_json(output_file, result)
    return result


def build_items_dataset(input_file: Path, output_file: Path) -> list[dict[str, Any]]:
    rows = json.loads(input_file.read_text(encoding="utf-8"))
    result = []
    for row in rows:
        page = row.get("Page") or row.get("_pageName") or "Unknown Item"
        result.append(
            {
                "name_zh": page,
                "name_en": page,
                "aliases": [],
                "obtain_methods": ["待从 Wiki 进一步同步"],
                "harvest_from": [],
                "best_tools": [],
                "item_code": row.get("ID", ""),
                "blueprint_path": row.get("Blueprint", ""),
                "notes": f"分类：{row.get('Category', '未知')}；堆叠：{row.get('stackSize', '未知')}；重量：{row.get('weight', '未知')}",
                "source_url": f"https://ark.wiki.gg/wiki/{urllib.parse.quote(str(page).replace(' ', '_'))}",
            }
        )
    write_json(output_file, result)
    return result


def build_resources_dataset(input_file: Path, output_file: Path) -> list[dict[str, Any]]:
    rows = json.loads(input_file.read_text(encoding="utf-8"))
    result = []
    for row in rows:
        page = row.get("Page") or row.get("_pageName") or "Unknown Resource"
        result.append(
            {
                "resource_name": page,
                "aliases": [],
                "map_name": "待补充",
                "areas": [],
                "coordinates": [],
                "risk_level": "待补充",
                "notes": "；".join(
                    [
                        f"稀有度：{row.get('Rarity', '未知')}",
                        f"可再生：{_to_bool_text(row.get('Renewable'))}",
                        f"可精炼：{_to_bool_text(row.get('Refineable'))}",
                        f"可燃烧：{_to_bool_text(row.get('Combustible'))}",
                    ]
                ),
                "source_url": f"https://ark.wiki.gg/wiki/{urllib.parse.quote(str(page).replace(' ', '_'))}",
            }
        )
    write_json(output_file, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync ARK wiki data into local plugin JSON files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("cargo-tables", help="List available Cargo tables.")

    fields_parser = subparsers.add_parser("cargo-fields", help="Inspect fields for a Cargo table.")
    fields_parser.add_argument("--table", required=True)

    export_parser = subparsers.add_parser("cargo-export", help="Export a Cargo query to JSON.")
    export_parser.add_argument("--table", required=True)
    export_parser.add_argument("--fields", required=True)
    export_parser.add_argument("--where", default="")
    export_parser.add_argument("--join-on", default="")
    export_parser.add_argument("--group-by", default="")
    export_parser.add_argument("--order-by", default="")
    export_parser.add_argument("--limit", type=int, default=500)
    export_parser.add_argument("--output", required=True)

    page_parser = subparsers.add_parser("page-html", help="Fetch parsed HTML for a wiki page.")
    page_parser.add_argument("--page", required=True)
    page_parser.add_argument("--output", required=True)
    page_parser.add_argument("--uselang", default="")

    links_parser = subparsers.add_parser("extract-links", help="Extract /wiki/... links from a parsed page payload.")
    links_parser.add_argument("--input", required=True)
    links_parser.add_argument("--output", required=True)
    links_parser.add_argument("--contains", default="")

    batch_parser = subparsers.add_parser("page-batch", help="Fetch a batch of pages into JSON payloads.")
    batch_parser.add_argument("--pages-json", required=True)
    batch_parser.add_argument("--output-dir", required=True)

    probe_parser = subparsers.add_parser("probe-asa", help="Probe Cargo tables and known ASA pages into a local snapshot.")
    probe_parser.add_argument("--output-dir", required=True)
    probe_parser.add_argument("--profile", default=str(DEFAULT_PROFILE_PATH))

    loot_master_parser = subparsers.add_parser("extract-loot-subpages", help="Extract loot-table subpage names from the Loot_tables master page payload.")
    loot_master_parser.add_argument("--master-input", required=True)
    loot_master_parser.add_argument("--output", required=True)

    preset_parser = subparsers.add_parser("cargo-export-preset", help="Run a predefined Cargo export preset from sync_profiles.json.")
    preset_parser.add_argument("--preset", required=True)
    preset_parser.add_argument("--output", required=True)
    preset_parser.add_argument("--profile", default=str(DEFAULT_PROFILE_PATH))

    build_creatures_parser = subparsers.add_parser("build-creatures-dataset", help="Transform raw creature Cargo export into plugin dataset shape.")
    build_creatures_parser.add_argument("--input", required=True)
    build_creatures_parser.add_argument("--output", required=True)

    build_items_parser = subparsers.add_parser("build-items-dataset", help="Transform raw item Cargo export into plugin dataset shape.")
    build_items_parser.add_argument("--input", required=True)
    build_items_parser.add_argument("--output", required=True)

    build_resources_parser = subparsers.add_parser("build-resources-dataset", help="Transform raw resource Cargo export into plugin dataset shape.")
    build_resources_parser.add_argument("--input", required=True)
    build_resources_parser.add_argument("--output", required=True)

    dossiers_parser = subparsers.add_parser("extract-dossiers-creature-map", help="Extract base creature Chinese names from a Dossiers page payload.")
    dossiers_parser.add_argument("--dossiers-input", required=True)
    dossiers_parser.add_argument("--creatures-input", required=True)
    dossiers_parser.add_argument("--output", required=True)

    langlinks_parser = subparsers.add_parser("fetch-langlinks", help="Fetch translated page titles for a list of titles.")
    langlinks_parser.add_argument("--titles-json", required=True)
    langlinks_parser.add_argument("--output", required=True)
    langlinks_parser.add_argument("--lang", default="zh")

    overrides_parser = subparsers.add_parser("build-creature-name-overrides", help="Build a creature translation and alias override map.")
    overrides_parser.add_argument("--creatures-input", required=True)
    overrides_parser.add_argument("--langlinks-input", required=True)
    overrides_parser.add_argument("--manual-overrides", default="")
    overrides_parser.add_argument("--output", required=True)

    base_overrides_parser = subparsers.add_parser("build-creature-name-overrides-from-base", help="Build creature Chinese overrides from parsed Dossiers base names and variant rules.")
    base_overrides_parser.add_argument("--creatures-input", required=True)
    base_overrides_parser.add_argument("--base-map-input", required=True)
    base_overrides_parser.add_argument("--manual-overrides", default="")
    base_overrides_parser.add_argument("--output", required=True)

    merge_translations_parser = subparsers.add_parser("merge-creature-translations", help="Merge translated creature names into a generated creature dataset.")
    merge_translations_parser.add_argument("--creatures-input", required=True)
    merge_translations_parser.add_argument("--overrides-input", required=True)
    merge_translations_parser.add_argument("--output", required=True)

    translation_report_parser = subparsers.add_parser("build-creature-translation-report", help="Build a creature translation coverage report and optional manual template.")
    translation_report_parser.add_argument("--creatures-input", required=True)
    translation_report_parser.add_argument("--translated-input", required=True)
    translation_report_parser.add_argument("--output", required=True)
    translation_report_parser.add_argument("--template-output", default="")

    autofill_translations_parser = subparsers.add_parser("autofill-creature-translations", help="Run the full creature Chinese translation autofill pipeline from Dossiers and manual overrides.")
    autofill_translations_parser.add_argument("--creatures-input", required=True)
    autofill_translations_parser.add_argument("--dossiers-input", required=True)
    autofill_translations_parser.add_argument("--manual-overrides", default="")
    autofill_translations_parser.add_argument("--base-map-output", required=True)
    autofill_translations_parser.add_argument("--overrides-output", required=True)
    autofill_translations_parser.add_argument("--translated-output", required=True)
    autofill_translations_parser.add_argument("--report-output", required=True)
    autofill_translations_parser.add_argument("--template-output", default="")

    loot_subpage_parser = subparsers.add_parser("parse-loot-subpage", help="Parse a loot-table subpage payload into crate-to-item rows.")
    loot_subpage_parser.add_argument("--input", required=True)
    loot_subpage_parser.add_argument("--page-name", required=True)
    loot_subpage_parser.add_argument("--output", required=True)

    loot_dataset_parser = subparsers.add_parser("build-loot-datasets", help="Build generated loot crate and loot item datasets from fetched loot subpage payloads.")
    loot_dataset_parser.add_argument("--pages-json", required=True)
    loot_dataset_parser.add_argument("--payload-dir", required=True)
    loot_dataset_parser.add_argument("--crates-output", required=True)
    loot_dataset_parser.add_argument("--items-output", required=True)

    rebuild_parser = subparsers.add_parser("rebuild-item-sources", help="Rebuild reverse item source index from loot data.")
    rebuild_parser.add_argument("--data-dir", required=True)
    rebuild_parser.add_argument("--output", required=True)

    return parser.parse_args()


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())


def _split_list_like(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    return [text]


def _to_bool_text(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return "是"
    if text in {"0", "false", "no"}:
        return "否"
    return "未知"


def _dedupe_list(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in result:
            result.append(text)
    return result


def _dedupe_dict_rows(rows: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in rows:
        key_parts = [str(row.get(field, "")).strip() for field in key_fields]
        key = "||".join(key_parts)
        if not key:
            continue
        if key not in merged:
            merged[key] = row
            continue
        existing = merged[key]
        for field, value in row.items():
            if field not in existing or existing[field] in ("", [], None):
                existing[field] = value
    return list(merged.values())


def _build_saddle_text(saddle: Any, saddle_level: Any) -> str:
    saddle_text = str(saddle or "").strip()
    level_text = str(saddle_level or "").strip()
    if not saddle_text or saddle_text.lower() == "none":
        return "无"
    if level_text:
        return f"{saddle_text}（约 {level_text} 级）"
    return saddle_text


def _to_simplified(text: str) -> str:
    clean = str(text or "").strip()
    if not clean:
        return ""
    if SIMPLIFIED_CONVERTER:
        return SIMPLIFIED_CONVERTER.convert(clean)
    return clean


def _normalize_english_lookup(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())


def _build_combined_base_name_map(
    dossier_base_map: dict[str, dict[str, str]],
    manual_overrides: dict[str, Any],
) -> dict[str, str]:
    base_name_map = {
        name_en: entry.get("simplified") or entry.get("traditional") or ""
        for name_en, entry in dossier_base_map.items()
        if entry.get("simplified") or entry.get("traditional")
    }
    for name_en, override in manual_overrides.items():
        zh_name = str(override.get("name_zh", "")).strip()
        if zh_name:
            base_name_map[name_en] = zh_name
    return base_name_map


def _lookup_base_name_zh(name_en: str, base_name_map: dict[str, str]) -> str:
    direct = str(base_name_map.get(name_en, "")).strip()
    if direct:
        return direct

    normalized = _normalize_english_lookup(name_en)
    alias_target = ENGLISH_BASE_ALIASES.get(normalized, "")
    if alias_target:
        alias_value = str(base_name_map.get(alias_target, "")).strip()
        if alias_value:
            return alias_value

    for key, value in base_name_map.items():
        if _normalize_english_lookup(key) == normalized and str(value).strip():
            return str(value).strip()

    return ""


def _translate_variant_name(name_en: str, base_name_map: dict[str, str], depth: int = 0) -> dict[str, list[str] | str]:
    if depth > 6:
        return {"name_zh": "", "aliases": []}

    direct = _lookup_base_name_zh(name_en, base_name_map)
    if direct:
        return {"name_zh": direct, "aliases": [direct]}

    prefix_rules = [
        ("Aberrant ", "畸变"),
        ("Alpha ", "精英"),
        ("Beta ", "贝塔"),
        ("Gamma ", "伽马"),
        ("Corrupted ", "腐化"),
        ("Experimental ", "实验体"),
        ("Tek ", "泰克"),
        ("Malfunctioned ", "故障"),
        ("Enraged ", "狂暴"),
        ("Skeletal ", "骸骨"),
        ("Skeleton ", "骸骨"),
        ("Ghost ", "幽灵"),
        ("Eerie ", "怪异"),
        ("Brute ", "残暴"),
        ("Infernal ", "炼狱"),
        ("Apex ", "顶级"),
        ("Fabled ", "传说"),
        ("Toxic ", "剧毒"),
        ("Celestial ", "天界"),
        ("Demonic ", "恶魔"),
        ("Abyssal ", "深渊"),
        ("Mutated ", "变异"),
        ("Astral ", "星界"),
        ("Revenant ", "亡魂"),
        ("Lightning ", "闪电"),
        ("Fire ", "火焰"),
        ("Water ", "水系"),
        ("Poison ", "毒系"),
        ("Crystal ", "水晶"),
        ("Blood Crystal ", "血晶"),
        ("Ember Crystal ", "余烬水晶"),
        ("Tropical Crystal ", "热带水晶"),
        ("Surface ", "地表"),
        ("Rockwell ", "罗克韦尔"),
        ("Lost ", "迷失"),
        ("Winter ", "冬季"),
        ("Summer ", "夏季"),
        ("Autumn ", "秋季"),
        ("Spring ", "春季"),
        ("Golden ", "黄金"),
        ("Giant ", "巨型"),
        ("Bunny ", "兔子"),
        ("Love ", "爱心"),
        ("Zombie ", "僵尸"),
        ("Elemental ", "元素"),
        ("Subterranean ", "地下"),
        ("Injured ", "受伤"),
        ("Succumbed ", "堕化"),
        ("Bloated ", "臃肿"),
        ("Dire ", "凶暴"),
        ("Golden Striped ", "金纹"),
        ("Rare ", "稀有"),
        ("Spirit ", "灵魂"),
        ("Party ", "派对"),
        ("Valentines ", "情人节"),
        ("Dodo ", "渡渡"),
        ("VR ", "VR "),
    ]
    suffix_rules = [
        (" Ghost", "幽灵", "prefix"),
        (" (Alpha)", "（Alpha）", "suffix"),
        (" (Beta)", "（Beta）", "suffix"),
        (" (Gamma)", "（Gamma）", "suffix"),
    ]
    exact_rules = [
        ("X-", "X-"),
        ("R-", "R-"),
    ]
    exact_name_rules = {
        **MANUAL_CREATURE_ZH,
        "DodoRex": "渡渡霸王龙",
        "Crystal Wyvern": "水晶飞龙",
        "Blood Crystal Wyvern": "血晶飞龙",
        "Ember Crystal Wyvern": "余烬水晶飞龙",
        "Tropical Crystal Wyvern": "热带水晶飞龙",
        "Fire Wyvern": "火焰飞龙",
        "Lightning Wyvern": "闪电飞龙",
        "Poison Wyvern": "毒飞龙",
        "Water Wyvern": "水飞龙",
        "Dodo Wyvern": "渡渡飞龙",
        "Forest Wyvern": "森林飞龙",
        "Zombie Wyvern": "僵尸飞龙",
        "Crystal Wyvern Queen": "水晶飞龙女王",
        "Lost King": "迷失之王",
        "Lost Queen": "迷失女王",
        "Rockwell Node": "罗克韦尔节点",
        "Rockwell Prime": "罗克韦尔本体",
        "Reaper": "死神",
        "Reaper King": "死神国王",
        "Reaper Queen": "死神女王",
        "Reaper Prince": "死神王子",
        "Reaper Offspring": "死神后代",
        "Thrall": "奴仆",
        "Moeder, Master of the Ocean": "海洋主宰莫德尔",
        "Revenant": "亡魂",
    }
    thrall_role_rules = {
        "Archer": "弓箭手",
        "Bounty Hunter": "赏金猎人",
        "Cavalry Commander": "骑兵指挥官",
        "Deadeye": "神射手",
        "Demolisher": "爆破手",
        "Enforcer": "执法者",
        "Forgemaster": "铸造大师",
        "Gunslinger": "枪手",
        "Herald": "先驱",
        "Marauder": "劫掠者",
        "Marksman": "射手",
        "Piercer": "穿刺者",
        "Scattershot": "散射手",
        "Snarer": "诱捕者",
        "Subjugator": "征服者",
        "Warden": "守卫者",
    }

    exact_name = exact_name_rules.get(name_en, "")
    if exact_name:
        return {"name_zh": exact_name, "aliases": [exact_name]}

    if name_en.startswith("Thrall "):
        role_name = name_en[len("Thrall ") :].strip()
        role_zh = thrall_role_rules.get(role_name, "")
        if role_zh:
            display_name = f"奴仆{role_zh}"
            return {"name_zh": display_name, "aliases": [display_name]}

    if name_en.startswith("Revenant "):
        suffix_name = name_en[len("Revenant ") :].strip()
        if suffix_name:
            translated = _translate_variant_name(suffix_name, base_name_map, depth + 1)
            base_zh = str(translated.get("name_zh", "")).strip()
            display_name = f"亡魂{base_zh or suffix_name}"
            return {"name_zh": display_name, "aliases": [display_name]}

    for prefix, zh_prefix in prefix_rules:
        if name_en.startswith(prefix):
            base_name = name_en[len(prefix) :].strip()
            translated = _translate_variant_name(base_name, base_name_map, depth + 1)
            base_zh = str(translated.get("name_zh", "")).strip()
            if base_zh:
                return {
                    "name_zh": f"{zh_prefix}{base_zh}",
                    "aliases": [f"{zh_prefix}{base_zh}"],
                }

    for suffix, zh_text, placement in suffix_rules:
        if name_en.endswith(suffix):
            base_name = name_en[: -len(suffix)].strip()
            translated = _translate_variant_name(base_name, base_name_map, depth + 1)
            base_zh = str(translated.get("name_zh", "")).strip()
            if base_zh:
                display_name = f"{zh_text}{base_zh}" if placement == "prefix" else f"{base_zh}{zh_text}"
                return {
                    "name_zh": display_name,
                    "aliases": [display_name],
                }

    for english_prefix, zh_prefix in exact_rules:
        if name_en.startswith(english_prefix):
            base_name = name_en[len(english_prefix) :].strip()
            translated = _translate_variant_name(base_name, base_name_map, depth + 1)
            base_zh = str(translated.get("name_zh", "")).strip()
            if base_zh:
                return {
                    "name_zh": f"{zh_prefix}{base_zh}",
                    "aliases": [f"{zh_prefix}{base_zh}"],
                }

    return {"name_zh": "", "aliases": []}


def main() -> int:
    args = parse_args()
    client = WikiClient()

    if args.command == "cargo-tables":
        print(json.dumps(client.cargo_tables(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "cargo-fields":
        print(json.dumps(client.cargo_fields(args.table), ensure_ascii=False, indent=2))
        return 0

    if args.command == "cargo-export":
        rows = client.cargo_query(
            table=args.table,
            fields=args.fields,
            where=args.where,
            join_on=args.join_on,
            group_by=args.group_by,
            order_by=args.order_by,
            limit=args.limit,
        )
        write_json(Path(args.output), rows)
        print(f"exported {len(rows)} rows to {args.output}")
        return 0

    if args.command == "page-html":
        payload = client.parse_page(args.page, uselang=args.uselang)
        write_json(Path(args.output), payload)
        print(f"saved parsed page to {args.output}")
        return 0

    if args.command == "extract-links":
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        links = extract_wiki_links_from_parse_payload(payload, contains=args.contains)
        write_json(Path(args.output), links)
        print(f"extracted {len(links)} links")
        return 0

    if args.command == "page-batch":
        pages = json.loads(Path(args.pages_json).read_text(encoding="utf-8"))
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for page in pages:
            payload = client.parse_page(str(page))
            filename = _safe_filename(str(page)) + ".json"
            write_json(output_dir / filename, payload)
        print(f"saved {len(pages)} page payloads")
        return 0

    if args.command == "probe-asa":
        manifest = probe_asa(client, Path(args.output_dir), Path(args.profile))
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    if args.command == "extract-loot-subpages":
        rows = extract_loot_subpages(Path(args.master_input), Path(args.output))
        print(f"generated {len(rows)} loot subpage names")
        return 0

    if args.command == "cargo-export-preset":
        profiles = load_profiles(Path(args.profile))
        preset = profiles.get("export_presets", {}).get(args.preset)
        if not preset:
            print(f"unknown preset: {args.preset}", file=sys.stderr)
            return 1
        rows = client.cargo_query(
            table=preset["table"],
            fields=preset["fields"],
            limit=500,
        )
        write_json(Path(args.output), rows)
        print(f"exported {len(rows)} rows with preset {args.preset}")
        return 0

    if args.command == "build-creatures-dataset":
        rows = build_creatures_dataset(Path(args.input), Path(args.output))
        print(f"generated {len(rows)} creature rows")
        return 0

    if args.command == "build-items-dataset":
        rows = build_items_dataset(Path(args.input), Path(args.output))
        print(f"generated {len(rows)} item rows")
        return 0

    if args.command == "build-resources-dataset":
        rows = build_resources_dataset(Path(args.input), Path(args.output))
        print(f"generated {len(rows)} resource rows")
        return 0

    if args.command == "extract-dossiers-creature-map":
        mapping = extract_dossiers_creature_map(
            Path(args.dossiers_input),
            Path(args.creatures_input),
            Path(args.output),
        )
        print(f"generated {len(mapping)} dossier creature name rows")
        return 0

    if args.command == "fetch-langlinks":
        titles = json.loads(Path(args.titles_json).read_text(encoding="utf-8"))
        mapping = fetch_langlinks_for_titles(client, titles, args.lang)
        write_json(Path(args.output), mapping)
        print(f"fetched {len(mapping)} langlinks")
        return 0

    if args.command == "build-creature-name-overrides":
        overrides = build_creature_name_overrides(
            Path(args.creatures_input),
            Path(args.langlinks_input),
            Path(args.manual_overrides) if args.manual_overrides else None,
            Path(args.output),
        )
        print(f"generated {len(overrides)} creature name overrides")
        return 0

    if args.command == "build-creature-name-overrides-from-base":
        overrides = build_creature_name_overrides_from_base_map(
            Path(args.creatures_input),
            Path(args.base_map_input),
            Path(args.manual_overrides) if args.manual_overrides else None,
            Path(args.output),
        )
        print(f"generated {len(overrides)} creature name overrides from base map")
        return 0

    if args.command == "merge-creature-translations":
        rows = merge_creature_translations(
            Path(args.creatures_input),
            Path(args.overrides_input),
            Path(args.output),
        )
        print(f"generated {len(rows)} translated creature rows")
        return 0

    if args.command == "build-creature-translation-report":
        report = build_creature_translation_report(
            Path(args.creatures_input),
            Path(args.translated_input),
            Path(args.output),
            template_output=Path(args.template_output) if args.template_output else None,
        )
        print(
            f"generated creature translation report: "
            f"{report['translated']}/{report['total']} translated "
            f"({report['coverage_ratio']:.2%})"
        )
        return 0

    if args.command == "autofill-creature-translations":
        report = autofill_creature_translations(
            Path(args.creatures_input),
            Path(args.dossiers_input),
            Path(args.manual_overrides) if args.manual_overrides else None,
            Path(args.base_map_output),
            Path(args.overrides_output),
            Path(args.translated_output),
            Path(args.report_output),
            template_output=Path(args.template_output) if args.template_output else None,
        )
        print(
            f"autofill complete: "
            f"{report['translated']}/{report['total']} translated "
            f"({report['coverage_ratio']:.2%})"
        )
        return 0

    if args.command == "parse-loot-subpage":
        rows = parse_loot_subpage(
            Path(args.input),
            args.page_name,
            Path(args.output),
        )
        print(f"generated {len(rows)} loot crate rows")
        return 0

    if args.command == "build-loot-datasets":
        crate_rows, item_rows = build_loot_datasets(
            Path(args.pages_json),
            Path(args.payload_dir),
            Path(args.crates_output),
            Path(args.items_output),
        )
        print(f"generated {len(crate_rows)} crate rows and {len(item_rows)} item rows")
        return 0

    if args.command == "rebuild-item-sources":
        result = rebuild_item_sources(Path(args.data_dir), Path(args.output))
        print(f"generated {len(result)} reverse source rows")
        return 0

    print("unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
