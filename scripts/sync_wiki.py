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
RESOURCE_NAME_OVERRIDES_EN_TO_ZH = {
    "black pearl": "黑珍珠",
    "blue gem": "蓝宝石",
    "crystal": "水晶",
    "element ore": "元素矿石",
    "fungal wood": "真菌木",
    "gas vein": "气脉",
    "green gem": "绿宝石",
    "metal": "金属",
    "metal (rich deposit)": "富金属矿",
    "obsidian": "黑曜石",
    "oil": "石油",
    "red gem": "红宝石",
    "salt": "盐",
    "sand": "沙子",
    "silica pearls": "硅珍珠",
    "sulfur": "硫磺",
}
MAP_NAME_EN_TO_ZH = {
    "The Island": "孤岛",
    "Scorched Earth": "焦土",
    "The Center": "中心岛",
    "Aberration": "畸变",
    "Extinction": "灭绝",
    "Ragnarok": "仙境",
    "Valguero": "瓦尔盖罗",
}
ARTIFACT_NAME_ZH = {
    "Artifact of Chaos": "混沌神器",
    "Artifact of Growth": "生长神器",
    "Artifact of the Brute": "强壮神器",
    "Artifact of the Clever": "聪明神器",
    "Artifact of the Crag": "峭壁神器",
    "Artifact of the Cunning": "狡诈神器",
    "Artifact of the Depths": "深渊神器",
    "Artifact of the Destroyer": "毁灭者神器",
    "Artifact of the Devious": "诡计神器",
    "Artifact of the Devourer": "吞噬神器",
    "Artifact of the Fallen": "陨落神器",
    "Artifact of the Gatekeeper": "守门人神器",
    "Artifact of the Hunter": "猎手神器",
    "Artifact of the Immune": "免疫神器",
    "Artifact of the Lost": "失落神器",
    "Artifact of the Massive": "巨型神器",
    "Artifact of the Mighty": "强大神器",
    "Artifact of the Pack": "群狼神器",
    "Artifact of the Seeking": "追寻者神器",
    "Artifact of the Shadows": "暗影神器",
    "Artifact of the Skylord": "天主神器",
    "Artifact of the Stalker": "潜行者神器",
    "Artifact of the Strong": "强者神器",
    "Artifact of the Void": "虚空神器",
    "Artifact Pedestal": "神器底座",
}
KIBBLE_NAME_ZH = {
    "Basic Kibble": "基础饲料",
    "Simple Kibble": "简易饲料",
    "Regular Kibble": "普通饲料",
    "Superior Kibble": "上等饲料",
    "Exceptional Kibble": "卓越饲料",
    "Extraordinary Kibble": "非凡饲料",
}
ITEM_FIXED_TRANSLATIONS = {
    "Absorbent Substrate": "吸收基质",
    "Achatina Paste": "玛瑙螺黏液",
    "Ambergris": "龙涎香",
    "Ammonite Bile": "菊石胆汁",
    "AnglerGel": "鮟鱇鱼发光凝胶",
    "Barnacle": "藤壶",
    "Element Dust": "元素粉尘",
    "Element Ore": "元素矿石",
    "Metal Ingot": "金属锭",
    "Organic Polymer": "有机聚合物",
    "Polymer": "聚合物",
    "Propellant": "推进剂",
    "Silica Pearls": "硅珍珠",
    "Sparkpowder": "火花粉",
}
ITEM_PHRASE_TRANSLATIONS = {
    "Primitive Plus": "Primitive Plus",
    "Platform Saddle": "平台鞍",
    "Tek Saddle": "泰克鞍",
    "Starwing Saddle": "星翼鞍",
    "Ghost Costume": "幽灵服装",
    "Bone Costume": "骨骼服装",
    "Bionic Costume": "仿生服装",
    "Corrupted Costume": "腐化服装",
    "Double Doorframe": "双门框",
    "Double Door": "双开门",
    "Dinosaur Gateway": "恐龙门框",
    "Dinosaur Gate": "恐龙门",
    "Fence Foundation": "栅栏地基",
    "Fence Support": "栅栏支柱",
    "Triangle Ceiling": "三角天花板",
    "Triangle Foundation": "三角地基",
    "Triangle Roof": "三角屋顶",
    "Windowframe": "窗框",
    "Doorframe": "门框",
    "Hatchframe": "天窗框",
    "Trapdoor": "活板门",
    "Swim Bottom Skin": "泳装下装皮肤",
    "Swim Shorts Skin": "泳裤皮肤",
    "Swim Top Skin": "泳装上衣皮肤",
    "Hat Skin": "帽子皮肤",
    "Helmet Skin": "头盔皮肤",
    "Shirt Skin": "衬衫皮肤",
    "Pants Skin": "裤子皮肤",
    "Mask Skin": "面具皮肤",
    "Club Skin": "木棒皮肤",
    "Sword Skin": "剑皮肤",
    "Pickaxe Skin": "镐子皮肤",
    "Hatchet Skin": "斧子皮肤",
    "Parachute Skin": "降落伞皮肤",
    "Rod Skin": "鱼竿皮肤",
    "Wall-Mount": "壁挂",
    "Mail Box": "邮箱",
    "Air Conditioner": "空调",
    "Ammo Box": "弹药箱",
    "Egg Incubator": "孵化器",
}
ITEM_TOKEN_TRANSLATIONS = {
    "Aberrant": "畸变",
    "Adobe": "土坯",
    "Advanced": "高级",
    "Admin": "管理员",
    "Air": "空气",
    "Alpha": "精英",
    "Animated": "动画版",
    "Aquatic": "水生",
    "Arctic": "极地",
    "ARK": "ARK",
    "Armor": "护甲",
    "Axe": "斧",
    "Backflip": "后空翻",
    "Baked": "烘焙",
    "Balloon": "气球",
    "Banner": "横幅",
    "Barrel": "桶",
    "Basic": "基础",
    "Battle": "战斗",
    "BearHug": "抱抱熊",
    "Behemoth": "巨型",
    "Belly": "肚皮",
    "Big": "大型",
    "Bionic": "仿生",
    "Blink": "闪现",
    "Blue": "蓝色",
    "Blood": "血",
    "Boat": "船",
    "Bone": "骨骼",
    "Boots": "靴子",
    "Bottom": "下装",
    "Bow": "弓",
    "Box": "箱",
    "Brick": "砖",
    "Broth": "肉汤",
    "Bullet": "子弹",
    "Bunny": "兔子",
    "Cage": "笼",
    "Cake": "蛋糕",
    "Camo": "迷彩",
    "Campfire": "篝火",
    "Candle": "蜡烛",
    "Candy": "糖果",
    "Cane": "甘蔗",
    "Captain's": "船长",
    "Caroling": "颂歌",
    "Ceiling": "天花板",
    "Chestpiece": "胸甲",
    "Chibi": "迷你",
    "Chick": "小鸡",
    "Chieftan": "酋长",
    "Chili": "辣椒",
    "Clap": "鼓掌",
    "Claw": "爪",
    "Club": "木棒",
    "Coat": "外套",
    "Coloring": "染料",
    "Companion": "伙伴",
    "Cooked": "熟",
    "Cool": "酷炫",
    "Corrupted": "腐化",
    "Costume": "服装",
    "Cupid": "丘比特",
    "Dance": "舞蹈",
    "Deal": "墨镜",
    "Dev": "开发者",
    "Door": "门",
    "Dough": "面团",
    "Double": "双",
    "Drums": "鼓",
    "Egg": "蛋",
    "Ears": "耳朵",
    "Easter": "复活节",
    "Elderclaw": "老爪",
    "Electric": "电",
    "Emote": "表情动作",
    "Exceptional": "卓越",
    "Extraordinary": "非凡",
    "Eyes": "眼睛",
    "Feather": "羽毛",
    "Fence": "栅栏",
    "Festive": "节庆",
    "File": "文件",
    "Fishing": "钓鱼",
    "Flag": "旗帜",
    "Flare": "信号",
    "Flex": "秀肌肉",
    "Foundation": "地基",
    "Fresh": "新鲜",
    "Gauntlets": "护手",
    "Gate": "门",
    "Gateway": "门框",
    "Ghost": "幽灵",
    "Gloves": "手套",
    "Goggles": "护目镜",
    "Graft": "嫁接",
    "Green": "绿色",
    "Greenhouse": "温室",
    "Grenade": "手雷",
    "Gunpowder": "火药",
    "Hair": "发型",
    "Happy": "开心",
    "Hat": "帽子",
    "Hatchet": "斧子",
    "Head": "头",
    "Heart": "爱心",
    "Helmet": "头盔",
    "Hide": "兽皮",
    "Honey": "蜂蜜",
    "Hop": "跳跃",
    "Hug": "拥抱",
    "Hula": "呼啦",
    "Human": "人类",
    "Incubator": "孵化器",
    "Industrial": "工业",
    "Jar": "罐",
    "Jaws": "颚骨",
    "Jerky": "肉干",
    "Juice": "果汁",
    "Kibble": "饲料",
    "King": "国王",
    "Kit": "套件",
    "Knock": "敲门",
    "Ladder": "梯子",
    "Large": "大型",
    "Leg": "腿",
    "Leggings": "护腿",
    "Lovely": "可爱",
    "Lost": "失落",
    "Lumber": "木材",
    "Mailbox": "邮箱",
    "Mail": "邮件",
    "Mask": "面具",
    "Mead": "蜂蜜酒",
    "Meat": "肉",
    "Metal": "金属",
    "Mobile": "Mobile",
    "Modern": "现代",
    "Mosh": "摇滚",
    "Mount": "底座",
    "Mushroom": "蘑菇",
    "Noglin-Print": "诺格林印花",
    "Note": "笔记",
    "Nutcracker": "胡桃夹子",
    "Oven": "烤炉",
    "Panic": "惊慌",
    "Pants": "裤子",
    "Parachute": "降落伞",
    "Party": "派对",
    "Pedestal": "底座",
    "Pickaxe": "镐子",
    "Pillar": "柱子",
    "Pit": "舞池",
    "Platform": "平台",
    "Print": "印花",
    "Proto": "原型",
    "Railing": "栏杆",
    "Ramp": "坡道",
    "Raw": "生",
    "Reindeer": "驯鹿",
    "Regular": "普通",
    "Rex": "霸王龙",
    "Rifle": "步枪",
    "Rig": "战车",
    "Roof": "屋顶",
    "Rub": "抚摸",
    "Rug": "地毯",
    "Saddle": "鞍",
    "Santa": "圣诞老人",
    "Scare": "惊吓",
    "Scout": "侦察兵",
    "Section": "段",
    "Seed": "种子",
    "Self": "自己",
    "Series": "系列",
    "Shirt": "衬衫",
    "Shorts": "短裤",
    "Simple": "简易",
    "Skin": "皮肤",
    "Slice": "切片",
    "Sloped": "斜面",
    "Small": "小型",
    "Smooch": "亲吻",
    "Snowball": "雪球",
    "Species": "物种",
    "Spike": "尖刺",
    "Stairs": "楼梯",
    "Staircase": "楼梯",
    "Statue": "雕像",
    "Stone": "石制",
    "Stronghold": "堡垒",
    "Sugar": "糖",
    "Suit": "套装",
    "Support": "支柱",
    "Surprise": "惊喜",
    "Survivor's": "幸存者",
    "Sword": "剑",
    "Table": "工作台",
    "Tail": "尾巴",
    "Tea": "茶",
    "Tek": "泰克",
    "Tester": "测试员",
    "Top": "上装",
    "Tophat": "高礼帽",
    "Trapdoor": "活板门",
    "Triangle": "三角",
    "Trophy": "战利品",
    "Turret": "炮塔",
    "Wall": "墙",
    "Wall-Mount": "壁挂",
    "Water": "水",
    "Weapon": "武器",
    "Whistle": "口哨",
    "Wiggle": "摇摆",
    "Wildcard": "Wildcard",
    "Window": "窗",
    "Winter": "冬季",
    "Wooden": "木制",
    "Work": "工作",
    "Workbench": "工作台",
    "Zombie": "僵尸",
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

    def query_datamap(
        self,
        page_id: int,
        revid: int | None = None,
        layers: list[str] | None = None,
        continue_token: str | None = None,
        limit: int | None = 500,
        sector: str | None = None,
        cb: str | int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "action": "queryDataMap",
            "pageid": str(page_id),
        }
        if revid is not None:
            params["revid"] = str(revid)
        if layers:
            params["layers"] = "|".join(layer for layer in layers if str(layer).strip())
        if continue_token:
            params["continue"] = str(continue_token)
        if limit:
            params["limit"] = str(limit)
        if sector:
            params["sector"] = str(sector)
        if cb not in (None, ""):
            params["cb"] = str(cb)
        return self.request(params)


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
    def _load_rows(name: str) -> list[dict[str, Any]]:
        path = data_dir / name
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _merge_rows(
        manual_name: str,
        generated_name: str,
        key_fields: tuple[str, ...],
        use_composite_key: bool = False,
    ) -> list[dict[str, Any]]:
        def make_key(row: dict[str, Any]) -> str:
            if use_composite_key:
                parts = []
                for field in key_fields:
                    value = str(row.get(field, "")).strip()
                    if value:
                        parts.append(f"{field}:{value}")
                return "|".join(parts)

            for field in key_fields:
                value = str(row.get(field, "")).strip()
                if value:
                    return f"{field}:{value}"
            return ""

        merged: dict[str, dict[str, Any]] = {}
        for row in _load_rows(generated_name):
            merge_key = make_key(row)
            if merge_key:
                merged[merge_key] = dict(row)

        for row in _load_rows(manual_name):
            merge_key = make_key(row)
            if not merge_key:
                continue
            if merge_key in merged:
                current = merged[merge_key]
                for key, value in row.items():
                    if isinstance(value, list):
                        current[key] = _dedupe_list(list(current.get(key, [])) + list(value))
                    elif value not in ("", None, [], {}):
                        current[key] = value
            else:
                merged[merge_key] = dict(row)
        return list(merged.values())

    loot_crates = _merge_rows(
        "loot_crates.json",
        "loot_crates.generated.json",
        ("crate_id", "name_en", "name_zh"),
    )
    loot_items = _merge_rows(
        "loot_crate_items.json",
        "loot_crate_items.generated.json",
        ("crate_id", "item_name_en", "item_name_zh"),
        use_composite_key=True,
    )
    items_rows = _merge_rows(
        "items.json",
        "items.generated.zh.json",
        ("item_code", "name_en", "name_zh"),
    )
    if not items_rows:
        items_rows = _merge_rows(
            "items.json",
            "items.generated.json",
            ("item_code", "name_en", "name_zh"),
        )

    crate_lookup = {row["crate_id"]: row for row in loot_crates}
    item_lookup = {
        _normalize_english_lookup(str(row.get("name_en", "")).strip()): row
        for row in items_rows
        if str(row.get("name_en", "")).strip()
    }
    grouped: dict[str, dict[str, Any]] = {}

    for row in loot_items:
        item_name_zh = row.get("item_name_zh", "")
        item_name_en = row.get("item_name_en", "")
        resolved_item = item_lookup.get(_normalize_english_lookup(item_name_en))
        if resolved_item:
            resolved_name_zh = str(resolved_item.get("name_zh", "")).strip()
            if resolved_name_zh and (not item_name_zh or item_name_zh == item_name_en):
                item_name_zh = resolved_name_zh
        key = item_name_en or item_name_zh
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
        if item_name_zh and item_name_zh != item_name_en:
            source["name_zh"] = item_name_zh
        if item_name_en and not source.get("name_en"):
            source["name_en"] = item_name_en

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


def localize_loot_crate_items(
    items_input: Path,
    loot_items_input: Path,
    output_file: Path,
) -> list[dict[str, Any]]:
    items_rows = json.loads(items_input.read_text(encoding="utf-8"))
    loot_items = json.loads(loot_items_input.read_text(encoding="utf-8"))
    item_lookup = {
        _normalize_english_lookup(str(row.get("name_en", "")).strip()): row
        for row in items_rows
        if str(row.get("name_en", "")).strip()
    }

    localized_rows: list[dict[str, Any]] = []
    for row in loot_items:
        current = dict(row)
        item_name_en = str(current.get("item_name_en", "")).strip()
        resolved = item_lookup.get(_normalize_english_lookup(item_name_en))
        if resolved:
            resolved_name_zh = str(resolved.get("name_zh", "")).strip()
            if resolved_name_zh:
                current["item_name_zh"] = resolved_name_zh
        localized_rows.append(current)

    write_json(output_file, localized_rows)
    return localized_rows


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


def _build_manual_item_name_map(manual_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in manual_items:
        name_en = str(row.get("name_en", "")).strip()
        if not name_en:
            continue
        aliases = _dedupe_list(list(row.get("aliases", [])))
        mapping[name_en] = {
            "name_zh": str(row.get("name_zh", "")).strip(),
            "aliases": aliases,
        }
    return mapping


def _build_creature_name_lookup(creatures_rows: list[dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in creatures_rows:
        name_zh = str(row.get("name_zh", "")).strip()
        if not name_zh:
            continue
        candidates = [row.get("name_en", ""), *row.get("aliases", [])]
        for candidate in candidates:
            key = _normalize_english_lookup(candidate)
            if key and key not in lookup:
                lookup[key] = name_zh
    return lookup


def _lookup_creature_item_name_zh(name_en: str, creature_lookup: dict[str, str]) -> str:
    direct = creature_lookup.get(_normalize_english_lookup(name_en), "")
    if direct:
        return direct

    normalized = _normalize_english_lookup(name_en)
    for key, value in creature_lookup.items():
        if key == normalized:
            return value
    return ""


def _translate_tokenized_item_name(name_en: str) -> str:
    result = str(name_en).strip()
    if not result:
        return ""

    for english, chinese in sorted(ITEM_PHRASE_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"\b{re.escape(english)}\b", chinese, result)

    for english, chinese in sorted(ITEM_TOKEN_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"\b{re.escape(english)}\b", chinese, result)

    result = re.sub(r"\s+", " ", result).strip()
    result = result.replace(" (", "（").replace(")", "）")
    result = result.replace(" - ", "-").replace(" :", ":")
    result = result.replace("Chibi-", "迷你")
    result = result.replace("Chibi ", "迷你")
    result = result.replace("Mobile:", "Mobile:")
    result = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", result)
    result = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-Za-z0-9])", "", result)
    result = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[\u4e00-\u9fff])", "", result)
    return result.strip()


def _looks_translated_item_name(name_en: str, candidate: str) -> bool:
    clean_candidate = str(candidate).strip()
    if not clean_candidate or clean_candidate == name_en:
        return False
    if not re.search(r"[\u4e00-\u9fff]", clean_candidate):
        return False

    english_words = re.findall(r"[A-Za-z]{3,}", clean_candidate)
    allowed_words = {"ARK", "Mobile", "Plus", "Primitive"}
    blocked = [word for word in english_words if word not in allowed_words]
    return len(blocked) <= 2


def _generate_item_name_zh(name_en: str, creature_lookup: dict[str, str]) -> tuple[str, list[str]]:
    clean_name = str(name_en or "").strip()
    if not clean_name:
        return "", []

    if clean_name in ITEM_FIXED_TRANSLATIONS:
        value = ITEM_FIXED_TRANSLATIONS[clean_name]
        return value, [value]

    if clean_name in ARTIFACT_NAME_ZH:
        value = ARTIFACT_NAME_ZH[clean_name]
        return value, [value]

    if clean_name in KIBBLE_NAME_ZH:
        value = KIBBLE_NAME_ZH[clean_name]
        return value, [value]

    primitive_plus_suffix = " (Primitive Plus)"
    if clean_name.endswith(primitive_plus_suffix):
        base_name = clean_name[: -len(primitive_plus_suffix)].strip()
        translated, aliases = _generate_item_name_zh(base_name, creature_lookup)
        if translated:
            value = f"{translated}（Primitive Plus）"
            return value, _dedupe_list([value, *aliases])

    kibble_match = re.fullmatch(r"Kibble \((.+?) Egg\)", clean_name)
    if kibble_match:
        creature_name = kibble_match.group(1).strip()
        creature_zh = _lookup_creature_item_name_zh(creature_name, creature_lookup)
        if creature_zh:
            value = f"{creature_zh}蛋饲料"
            return value, [value]

    for suffix, suffix_zh in [
        (" Platform Saddle", "平台鞍"),
        (" Tek Saddle", "泰克鞍"),
        (" Starwing Saddle", "星翼鞍"),
        (" Saddle", "鞍"),
        (" Egg", "蛋"),
        (" Trophy", "战利品"),
        (" Brain", "大脑"),
        (" Talon", "爪"),
        (" Claw", "爪"),
        (" Claws", "爪"),
        (" Fang", "獠牙"),
        (" Tooth", "牙"),
        (" Arm", "手臂"),
        (" Skull", "头骨"),
        (" Barb", "刺"),
        (" Fin", "鳍"),
        (" Eye", "眼"),
        (" Blubber", "脂"),
        (" Scale", "鳞片"),
        (" Horn", "角"),
        (" Horns", "角"),
        (" Spike", "尖刺"),
        (" Bile", "胆汁"),
        (" Gland", "腺体"),
        (" Pheromone", "信息素"),
        (" Ghost Costume", "幽灵服装"),
        (" Bone Costume", "骨骼服装"),
        (" Bionic Costume", "仿生服装"),
        (" Corrupted Costume", "腐化服装"),
        (" Costume", "服装"),
    ]:
        if clean_name.endswith(suffix):
            base_name = clean_name[: -len(suffix)].strip()
            creature_zh = _lookup_creature_item_name_zh(base_name, creature_lookup)
            if creature_zh:
                value = f"{creature_zh}{suffix_zh}"
                return value, [value]

    if clean_name.startswith("Chibi-") or clean_name.startswith("Chibi "):
        base_name = clean_name.replace("Chibi-", "", 1).replace("Chibi ", "", 1).strip()
        translated_base = _lookup_creature_item_name_zh(base_name, creature_lookup) or _translate_tokenized_item_name(base_name)
        if translated_base and _looks_translated_item_name(base_name, translated_base):
            value = f"迷你{translated_base}"
            return value, [value]

    translated = _translate_tokenized_item_name(clean_name)
    if _looks_translated_item_name(clean_name, translated):
        aliases = [translated]
        no_space_variant = translated.replace(" ", "")
        if no_space_variant != translated:
            aliases.append(no_space_variant)
        return translated, _dedupe_list(aliases)

    return "", []


def merge_item_translations(
    items_input: Path,
    langlinks_input: Path,
    manual_items_input: Path | None,
    creatures_input: Path | None,
    output_file: Path,
) -> list[dict[str, Any]]:
    items = json.loads(items_input.read_text(encoding="utf-8"))
    langlinks = json.loads(langlinks_input.read_text(encoding="utf-8"))
    manual_items = []
    if manual_items_input and manual_items_input.exists():
        manual_items = json.loads(manual_items_input.read_text(encoding="utf-8"))
    manual_lookup = _build_manual_item_name_map(manual_items)
    creatures_rows = []
    if creatures_input and creatures_input.exists():
        creatures_rows = json.loads(creatures_input.read_text(encoding="utf-8"))
    creature_lookup = _build_creature_name_lookup(creatures_rows)

    merged_rows: list[dict[str, Any]] = []
    for row in items:
        current = dict(row)
        name_en = str(current.get("name_en", "")).strip()
        translated = str(langlinks.get(name_en, "")).replace("_", " ").strip()
        manual_entry = manual_lookup.get(name_en, {})
        manual_name_zh = str(manual_entry.get("name_zh", "")).strip()
        generated_name_zh, generated_aliases = _generate_item_name_zh(name_en, creature_lookup)
        zh_name = translated or manual_name_zh or generated_name_zh or str(current.get("name_zh", "")).strip()
        aliases = _dedupe_list(list(current.get("aliases", [])) + list(manual_entry.get("aliases", [])))
        aliases = _dedupe_list(aliases + generated_aliases)
        if zh_name:
            current["name_zh"] = zh_name
            aliases = _dedupe_list([zh_name, *aliases])
        current["aliases"] = aliases
        merged_rows.append(current)

    write_json(output_file, merged_rows)
    return merged_rows


def build_item_translation_report(
    items_input: Path,
    translated_input: Path,
    output_file: Path,
    template_output: Path | None = None,
) -> dict[str, Any]:
    base_rows = json.loads(items_input.read_text(encoding="utf-8"))
    translated_rows = json.loads(translated_input.read_text(encoding="utf-8"))
    translated_lookup = {
        str(row.get("name_en", "")).strip(): row
        for row in translated_rows
        if str(row.get("name_en", "")).strip()
    }

    missing_rows: list[dict[str, str]] = []
    translated_count = 0
    for row in base_rows:
        name_en = str(row.get("name_en", "")).strip()
        translated_row = translated_lookup.get(name_en, {})
        name_zh = str(translated_row.get("name_zh", "")).strip()
        if name_zh and name_zh != name_en:
            translated_count += 1
        else:
            missing_rows.append({"name_en": name_en, "name_zh": ""})

    total = len(base_rows)
    report = {
        "total": total,
        "translated": translated_count,
        "missing": len(missing_rows),
        "coverage_ratio": (translated_count / total) if total else 0.0,
    }
    write_json(output_file, report)
    if template_output is not None:
        write_json(template_output, missing_rows)
    return report


def autofill_item_translations(
    client: WikiClient,
    items_input: Path,
    manual_items_input: Path | None,
    creatures_input: Path | None,
    langlinks_output: Path,
    translated_output: Path,
    report_output: Path,
    template_output: Path | None = None,
) -> dict[str, Any]:
    items = json.loads(items_input.read_text(encoding="utf-8"))
    titles = [
        str(row.get("name_en", "")).strip()
        for row in items
        if str(row.get("name_en", "")).strip()
    ]
    mapping = fetch_langlinks_for_titles(client, titles, "zh")
    write_json(langlinks_output, mapping)
    merge_item_translations(items_input, langlinks_output, manual_items_input, creatures_input, translated_output)
    return build_item_translation_report(
        items_input,
        translated_output,
        report_output,
        template_output=template_output,
    )


def _extract_datamap_config(parse_payload: dict[str, Any]) -> dict[str, Any]:
    text = parse_payload.get("parse", {}).get("text", "")
    if isinstance(text, dict):
        text = text.get("*", "")
    html_text = str(text)

    datamap_id_match = re.search(r'data-datamap-id="(\d+)"', html_text)
    config_match = re.search(
        r'<script type="application/datamap\+json" data-purpose="config">(.*?)</script>',
        html_text,
        re.I | re.S,
    )
    config = {}
    if config_match:
        config = json.loads(html.unescape(config_match.group(1)))

    return {
        "page": parse_payload.get("parse", {}).get("title", ""),
        "pageid": parse_payload.get("parse", {}).get("pageid"),
        "datamap_id": int(datamap_id_match.group(1)) if datamap_id_match else None,
        "config": config,
    }


def _extract_datamap_markers(payload: Any) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []

    if isinstance(payload, dict):
        grouped_markers = payload.get("query", {}).get("markers")
        if isinstance(grouped_markers, dict):
            for group_name, entries in grouped_markers.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if not isinstance(entry, list) or len(entry) < 2:
                        continue
                    marker: dict[str, Any] = {
                        "group": str(group_name).strip(),
                        "lat": entry[0],
                        "lng": entry[1],
                    }
                    if len(entry) >= 3 and isinstance(entry[2], dict):
                        marker.update(entry[2])
                    markers.append(marker)
            if markers:
                return markers

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return

        keys = set(node.keys())
        if (
            {"group", "lat", "lng"} <= keys
            or {"group", "x", "y"} <= keys
            or {"g", "x", "y"} <= keys
            or "markers" in keys
        ):
            if {"group", "lat", "lng"} <= keys or {"group", "x", "y"} <= keys or {"g", "x", "y"} <= keys:
                markers.append(node)
            for value in node.values():
                visit(value)
            return

        for value in node.values():
            visit(value)

    visit(payload)
    return markers


def _extract_datamap_continue_token(payload: dict[str, Any]) -> str:
    for key in ("continue", "continuation", "next"):
        value = payload.get(key)
        if value not in (None, "", 0):
            return str(value)

    for nested_key in ("query", "queryDataMap", "data"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            for key in ("continue", "continuation", "next"):
                value = nested.get(key)
                if value not in (None, "", 0):
                    return str(value)
    return ""


def fetch_datamap_markers(
    client: WikiClient,
    page: str,
    output_file: Path,
    layers: list[str] | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    parse_payload = client.parse_page(page)
    config_info = _extract_datamap_config(parse_payload)
    datamap_id = config_info.get("datamap_id")
    config = config_info.get("config", {})
    if not datamap_id:
        raise RuntimeError(f"did not find datamap id for page: {page}")

    revid = config.get("version")
    cb = config.get("lastPurgeTimestamp") or 0
    markers: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []
    seen_tokens: set[str] = set()
    continue_token = ""

    while True:
        payload = client.query_datamap(
            page_id=int(datamap_id),
            revid=int(revid) if revid not in (None, "") else None,
            layers=layers,
            continue_token=continue_token or None,
            limit=limit,
            cb=cb,
        )
        raw_pages.append(payload)
        markers.extend(_extract_datamap_markers(payload))

        next_token = _extract_datamap_continue_token(payload)
        if not next_token or next_token in seen_tokens:
            break
        seen_tokens.add(next_token)
        continue_token = next_token

    result = {
        "page": page,
        "map_name": str(page).split("/", 1)[1].replace("_", " ") if "/" in str(page) else str(page),
        "datamap_id": datamap_id,
        "config": config,
        "marker_count": len(markers),
        "markers": markers,
        "raw_pages": raw_pages,
    }
    write_json(output_file, result)
    return result


def fetch_datamap_markers_batch(
    client: WikiClient,
    pages_json: Path,
    output_dir: Path,
    limit: int = 500,
) -> list[dict[str, Any]]:
    pages = json.loads(pages_json.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    for page in pages:
        output_file = output_dir / f"{_safe_filename(str(page))}.json"
        result = fetch_datamap_markers(client, str(page), output_file, limit=limit)
        manifest.append(
            {
                "page": str(page),
                "output": str(output_file),
                "marker_count": result.get("marker_count", 0),
            }
        )

    return manifest


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _normalize_marker_coordinates(marker: dict[str, Any]) -> tuple[float | None, float | None]:
    if isinstance(marker.get("position"), list) and len(marker["position"]) >= 2:
        return _to_float(marker["position"][0]), _to_float(marker["position"][1])
    if isinstance(marker.get("pos"), list) and len(marker["pos"]) >= 2:
        return _to_float(marker["pos"][0]), _to_float(marker["pos"][1])

    x = _to_float(marker.get("x"))
    y = _to_float(marker.get("y"))
    if x is not None or y is not None:
        return x, y

    lng = _to_float(marker.get("lng"))
    lat = _to_float(marker.get("lat"))
    if lng is not None or lat is not None:
        return lng, lat

    return None, None


def _format_marker_coordinate(x: float | None, y: float | None) -> str:
    if x is None or y is None:
        return ""
    return f"{y:.1f},{x:.1f}"


def _build_item_translation_lookup(items_rows: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in items_rows:
        name_en = str(row.get("name_en", "")).strip()
        name_zh = str(row.get("name_zh", "")).strip()
        if not name_zh or name_zh == name_en:
            continue
        for candidate in [name_en, name_zh, *row.get("aliases", [])]:
            key = _normalize_english_lookup(candidate)
            if key and key not in mapping:
                mapping[key] = name_zh
    return mapping


def _build_resource_translation_lookup(
    resources_rows: list[dict[str, Any]],
    items_rows: list[dict[str, Any]],
) -> dict[str, str]:
    mapping = {
        _normalize_english_lookup(name): value
        for name, value in RESOURCE_NAME_OVERRIDES_EN_TO_ZH.items()
    }

    for row in resources_rows:
        name_zh = str(row.get("resource_name", "")).strip()
        if not name_zh:
            continue
        for candidate in [name_zh, *row.get("aliases", [])]:
            key = _normalize_english_lookup(candidate)
            if key and key not in mapping:
                mapping[key] = name_zh

    for key, value in _build_item_translation_lookup(items_rows).items():
        mapping.setdefault(key, value)

    return mapping


def build_resource_map_dataset(
    pages_json: Path,
    payload_dir: Path,
    resources_input: Path,
    items_input: Path,
    output_file: Path,
) -> list[dict[str, Any]]:
    pages = json.loads(pages_json.read_text(encoding="utf-8"))
    resources_rows = json.loads(resources_input.read_text(encoding="utf-8")) if resources_input.exists() else []
    items_rows = json.loads(items_input.read_text(encoding="utf-8")) if items_input.exists() else []
    translation_lookup = _build_resource_translation_lookup(resources_rows, items_rows)

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    excluded_groups = {"blue obelisk", "green obelisk", "red obelisk", "cave entrance"}

    for page in pages:
        payload_path = payload_dir / f"{_safe_filename(str(page))}.json"
        if not payload_path.exists():
            continue

        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        raw_map_name = str(payload.get("map_name", "") or str(page).split("/", 1)[1].replace("_", " ")).strip()
        map_name = MAP_NAME_EN_TO_ZH.get(raw_map_name, raw_map_name)
        config = payload.get("config", {})
        group_meta = config.get("groups", {})

        for marker in payload.get("markers", []):
            group_id = str(marker.get("group") or marker.get("g") or "").strip()
            group_name_en = str(
                marker.get("label")
                or marker.get("name")
                or group_meta.get(group_id, {}).get("name")
                or group_id
            ).strip()
            if not group_name_en:
                continue
            if group_name_en.lower() in excluded_groups:
                continue

            group_key = _normalize_english_lookup(group_name_en)
            resource_name = translation_lookup.get(group_key, group_name_en)
            row_key = (map_name, resource_name)
            row = grouped.setdefault(
                row_key,
                {
                    "map_name": map_name,
                    "resource_name": resource_name,
                    "aliases": _dedupe_list([group_name_en]),
                    "areas": [],
                    "coordinates": [],
                    "risk_level": "待补充",
                    "notes": f"自动同步自 {page}",
                    "source_url": f"https://ark.wiki.gg/wiki/{urllib.parse.quote(str(page).replace(' ', '_'))}",
                    "resource_name_en": group_name_en,
                    "node_count": 0,
                },
            )
            row["aliases"] = _dedupe_list(list(row.get("aliases", [])) + [group_name_en])
            row["node_count"] = int(row.get("node_count", 0)) + 1

            x, y = _normalize_marker_coordinates(marker)
            coordinate = _format_marker_coordinate(x, y)
            if coordinate:
                row["coordinates"] = _dedupe_list(list(row.get("coordinates", [])) + [coordinate])

        for row in grouped.values():
            if row["map_name"] != map_name:
                continue
            if row.get("node_count"):
                row["areas"] = [f"共 {row['node_count']} 个资源点"]
                shown = min(len(row.get("coordinates", [])), 12)
                row["notes"] = f"自动同步资源点数据，共 {row['node_count']} 个点位，当前保留前 {shown} 个坐标示例。"
                row["coordinates"] = list(row.get("coordinates", []))[:12]

    result = sorted(grouped.values(), key=lambda row: (str(row.get("resource_name", "")), str(row.get("map_name", ""))))
    write_json(output_file, result)
    return result


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

    merge_item_translations_parser = subparsers.add_parser("merge-item-translations", help="Merge translated item names into a generated item dataset.")
    merge_item_translations_parser.add_argument("--items-input", required=True)
    merge_item_translations_parser.add_argument("--langlinks-input", required=True)
    merge_item_translations_parser.add_argument("--manual-items", default="")
    merge_item_translations_parser.add_argument("--creatures-input", default="")
    merge_item_translations_parser.add_argument("--output", required=True)

    item_translation_report_parser = subparsers.add_parser("build-item-translation-report", help="Build an item translation coverage report and optional manual template.")
    item_translation_report_parser.add_argument("--items-input", required=True)
    item_translation_report_parser.add_argument("--translated-input", required=True)
    item_translation_report_parser.add_argument("--output", required=True)
    item_translation_report_parser.add_argument("--template-output", default="")

    autofill_item_translations_parser = subparsers.add_parser("autofill-item-translations", help="Run the full item Chinese translation autofill pipeline from langlinks and manual item names.")
    autofill_item_translations_parser.add_argument("--items-input", required=True)
    autofill_item_translations_parser.add_argument("--manual-items", default="")
    autofill_item_translations_parser.add_argument("--creatures-input", default="")
    autofill_item_translations_parser.add_argument("--langlinks-output", required=True)
    autofill_item_translations_parser.add_argument("--translated-output", required=True)
    autofill_item_translations_parser.add_argument("--report-output", required=True)
    autofill_item_translations_parser.add_argument("--template-output", default="")

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

    localize_loot_items_parser = subparsers.add_parser("localize-loot-crate-items", help="Backfill Chinese item names into generated loot crate item rows.")
    localize_loot_items_parser.add_argument("--items-input", required=True)
    localize_loot_items_parser.add_argument("--loot-items-input", required=True)
    localize_loot_items_parser.add_argument("--output", required=True)

    datamap_parser = subparsers.add_parser("fetch-datamap-markers", help="Fetch marker payloads for a resource data map page.")
    datamap_parser.add_argument("--page", required=True)
    datamap_parser.add_argument("--output", required=True)
    datamap_parser.add_argument("--limit", type=int, default=500)

    datamap_batch_parser = subparsers.add_parser("fetch-datamap-markers-batch", help="Fetch marker payloads for a batch of resource data map pages.")
    datamap_batch_parser.add_argument("--pages-json", required=True)
    datamap_batch_parser.add_argument("--output-dir", required=True)
    datamap_batch_parser.add_argument("--limit", type=int, default=500)

    resource_map_dataset_parser = subparsers.add_parser("build-resource-map-dataset", help="Build generated map resource rows from fetched datamap marker payloads.")
    resource_map_dataset_parser.add_argument("--pages-json", required=True)
    resource_map_dataset_parser.add_argument("--payload-dir", required=True)
    resource_map_dataset_parser.add_argument("--resources-input", required=True)
    resource_map_dataset_parser.add_argument("--items-input", required=True)
    resource_map_dataset_parser.add_argument("--output", required=True)

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

    if args.command == "merge-item-translations":
        rows = merge_item_translations(
            Path(args.items_input),
            Path(args.langlinks_input),
            Path(args.manual_items) if args.manual_items else None,
            Path(args.creatures_input) if args.creatures_input else None,
            Path(args.output),
        )
        print(f"generated {len(rows)} translated item rows")
        return 0

    if args.command == "build-item-translation-report":
        report = build_item_translation_report(
            Path(args.items_input),
            Path(args.translated_input),
            Path(args.output),
            template_output=Path(args.template_output) if args.template_output else None,
        )
        print(
            f"generated item translation report: "
            f"{report['translated']}/{report['total']} translated "
            f"({report['coverage_ratio']:.2%})"
        )
        return 0

    if args.command == "autofill-item-translations":
        report = autofill_item_translations(
            client,
            Path(args.items_input),
            Path(args.manual_items) if args.manual_items else None,
            Path(args.creatures_input) if args.creatures_input else None,
            Path(args.langlinks_output),
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

    if args.command == "localize-loot-crate-items":
        rows = localize_loot_crate_items(
            Path(args.items_input),
            Path(args.loot_items_input),
            Path(args.output),
        )
        print(f"localized {len(rows)} loot crate item rows")
        return 0

    if args.command == "fetch-datamap-markers":
        result = fetch_datamap_markers(
            client,
            args.page,
            Path(args.output),
            limit=args.limit,
        )
        print(f"fetched {result.get('marker_count', 0)} datamap markers")
        return 0

    if args.command == "fetch-datamap-markers-batch":
        manifest = fetch_datamap_markers_batch(
            client,
            Path(args.pages_json),
            Path(args.output_dir),
            limit=args.limit,
        )
        print(f"fetched {len(manifest)} datamap payloads")
        return 0

    if args.command == "build-resource-map-dataset":
        rows = build_resource_map_dataset(
            Path(args.pages_json),
            Path(args.payload_dir),
            Path(args.resources_input),
            Path(args.items_input),
            Path(args.output),
        )
        print(f"generated {len(rows)} resource map rows")
        return 0

    if args.command == "rebuild-item-sources":
        result = rebuild_item_sources(Path(args.data_dir), Path(args.output))
        print(f"generated {len(result)} reverse source rows")
        return 0

    print("unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
