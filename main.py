from __future__ import annotations

from pathlib import Path
from typing import Callable

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.config.astrbot_config import AstrBotConfig

from .services.query_service import ArkQueryService, QueryResult


DEFAULT_LLM_QUERY_SYSTEM_PROMPT = """你是一个 ARK: Survival Ascended 中文助手。
请优先根据插件提供的本地资料回答，保持简洁、准确、可执行。
如果本地资料不足，请明确说明“以下部分基于通用经验推断”，不要把推断说成已确认事实。
如果用户的问题本质上是在问驯服、代码、资源点、地图、宝箱、掉落或材料来源，请优先给出直接答案。"""


def _safe_config_get(config: AstrBotConfig, key: str, default):
    try:
        return config.get(key, default)
    except Exception:
        pass

    try:
        return config[key]
    except Exception:
        return default


class ArkAsaWikiPlugin(Star):
    """ARK: Survival Ascended local knowledge base plugin for AstrBot."""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        self.config = config
        self.enable_llm_query = bool(_safe_config_get(config, "enable_llm_query", True))
        self.llm_query_provider_id = str(_safe_config_get(config, "llm_query_provider_id", "")).strip()
        self.llm_query_max_context_chars = int(_safe_config_get(config, "llm_query_max_context_chars", 4000))
        self.llm_query_max_sections = int(_safe_config_get(config, "llm_query_max_sections", 6))
        self.llm_query_system_prompt = str(
            _safe_config_get(config, "llm_query_system_prompt", DEFAULT_LLM_QUERY_SYSTEM_PROMPT)
        ).strip() or DEFAULT_LLM_QUERY_SYSTEM_PROMPT
        self.service = ArkQueryService(
            plugin_dir=Path(__file__).resolve().parent,
            max_suggestions=int(_safe_config_get(config, "max_suggestions", 3)),
            show_source_url=bool(_safe_config_get(config, "show_source_url", True)),
            max_crate_items_display=int(_safe_config_get(config, "max_crate_items_display", 12)),
            show_map_status=bool(_safe_config_get(config, "show_map_status", True)),
            list_default_limit=int(_safe_config_get(config, "list_default_limit", 15)),
            allow_runtime_alias_edit=bool(_safe_config_get(config, "allow_runtime_alias_edit", True)),
            alias_storage_filename=str(_safe_config_get(config, "alias_storage_filename", "custom_aliases.json")),
            fuzzy_cjk_cutoff=float(_safe_config_get(config, "fuzzy_cjk_cutoff", 0.72)),
            fuzzy_latin_cutoff=float(_safe_config_get(config, "fuzzy_latin_cutoff", 0.6)),
        )
        logger.info("[ARK ASA] plugin loaded")

    @filter.command("ark")
    async def ark_command(self, event: AstrMessageEvent):
        async for result in self._dispatch_ark(event):
            yield result

    @filter.command("方舟")
    async def ark_cn_command(self, event: AstrMessageEvent):
        async for result in self._dispatch_ark(event):
            yield result

    @filter.command("驯龙")
    async def tame_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "tame"):
            yield result

    @filter.command("代码")
    async def code_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "code"):
            yield result

    @filter.command("材料")
    async def item_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "item"):
            yield result

    @filter.command("资源")
    async def resource_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "resource"):
            yield result

    @filter.command("地图")
    async def map_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "map"):
            yield result

    @filter.command("宝箱")
    async def crate_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "crate"):
            yield result

    @filter.command("掉落")
    async def loot_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "loot"):
            yield result

    @filter.command("来源")
    async def source_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "source"):
            yield result

    @filter.command("列表")
    async def list_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "list"):
            yield result

    @filter.command("别名")
    async def alias_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "alias"):
            yield result

    @filter.command("地图列表")
    async def maps_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "maps"):
            yield result

    @filter.command("方舟问答")
    async def ai_cn_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "ai"):
            yield result

    @filter.command("arkai")
    async def ai_command(self, event: AstrMessageEvent):
        async for result in self._run_simple(event, "ai"):
            yield result

    async def _dispatch_ark(self, event: AstrMessageEvent):
        raw = (event.message_str or "").strip()
        parts = raw.split(maxsplit=2)

        if len(parts) == 1:
            yield event.plain_result(self.service.help_text())
            return

        subcommand = parts[1].strip().lower()
        argument = parts[2].strip() if len(parts) > 2 else ""

        if subcommand in {"ai", "ask", "chat", "问答", "智能", "智能问答"}:
            yield event.plain_result(await self._query_with_llm(event, argument))
            return

        mapping: dict[str, Callable[[str], QueryResult]] = {
            "help": lambda _: self.service.help_result(),
            "帮助": lambda _: self.service.help_result(),
            "tame": self.service.query_tame,
            "驯养": self.service.query_tame,
            "驯龙": self.service.query_tame,
            "code": self.service.query_code,
            "代码": self.service.query_code,
            "item": self.service.query_item,
            "材料": self.service.query_item,
            "resource": self.service.query_resource,
            "资源": self.service.query_resource,
            "map": self.service.query_map,
            "地图": self.service.query_map,
            "maps": self.service.query_maps,
            "地图列表": self.service.query_maps,
            "crate": self.service.query_crate,
            "宝箱": self.service.query_crate,
            "loot": self.service.query_loot,
            "掉落": self.service.query_loot,
            "source": self.service.query_source,
            "来源": self.service.query_source,
            "list": self.service.query_list,
            "列表": self.service.query_list,
            "alias": self.service.query_alias,
            "别名": self.service.query_alias,
        }

        handler = mapping.get(subcommand)
        if handler is None:
            fallback = self.service.smart_query(" ".join(parts[1:]))
            yield event.plain_result(fallback.message)
            return

        result = handler(argument)
        yield event.plain_result(result.message)

    async def _run_simple(self, event: AstrMessageEvent, mode: str):
        raw = (event.message_str or "").strip()
        parts = raw.split(maxsplit=1)
        argument = parts[1].strip() if len(parts) > 1 else ""

        if mode == "tame":
            result = self.service.query_tame(argument)
        elif mode == "code":
            result = self.service.query_code(argument)
        elif mode == "item":
            result = self.service.query_item(argument)
        elif mode == "resource":
            result = self.service.query_resource(argument)
        elif mode == "map":
            result = self.service.query_map(argument)
        elif mode == "crate":
            result = self.service.query_crate(argument)
        elif mode == "loot":
            result = self.service.query_loot(argument)
        elif mode == "source":
            result = self.service.query_source(argument)
        elif mode == "list":
            result = self.service.query_list(argument)
        elif mode == "alias":
            result = self.service.query_alias(argument)
        elif mode == "maps":
            result = self.service.query_maps(argument)
        elif mode == "ai":
            yield event.plain_result(await self._query_with_llm(event, argument))
            return
        else:
            result = self.service.help_result()

        yield event.plain_result(result.message)

    async def _query_with_llm(self, event: AstrMessageEvent, question: str) -> str:
        prompt = (question or "").strip()
        if not prompt:
            return "用法：/ark ai 你的问题\n示例：/ark ai 高棘龙怎么驯服？"

        if not self.enable_llm_query:
            fallback = self.service.smart_query(prompt)
            if fallback.found:
                return fallback.message
            return "当前插件已关闭 LLM 智能问答，请联系管理员开启 enable_llm_query。"

        provider_id = await self._resolve_chat_provider_id(event)
        if not provider_id:
            fallback = self.service.smart_query(prompt)
            if fallback.found:
                return fallback.message
            return "当前会话没有可用的对话模型，暂时只能使用普通查询命令。"

        reference_text = self.service.build_llm_context(
            prompt,
            max_sections=max(1, self.llm_query_max_sections),
            max_chars=max(800, self.llm_query_max_context_chars),
        )
        llm_prompt = self._build_llm_prompt(prompt, reference_text)

        try:
            llm_response = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=llm_prompt,
                system_prompt=self.llm_query_system_prompt,
            )
            completion_text = str(getattr(llm_response, "completion_text", "") or "").strip()
            if completion_text:
                return completion_text
            raise RuntimeError("empty llm response")
        except Exception as exc:
            logger.exception("[ARK ASA] llm query failed")
            fallback = self.service.smart_query(prompt)
            if fallback.found:
                return f"{fallback.message}\n\n[提示] LLM 调用失败，已自动回退到本地资料查询。"
            error_text = str(exc).strip() or exc.__class__.__name__
            return f"LLM 调用失败：{error_text}"

    async def _resolve_chat_provider_id(self, event: AstrMessageEvent) -> str:
        if self.llm_query_provider_id:
            return self.llm_query_provider_id
        try:
            return str(await self.context.get_current_chat_provider_id(event.unified_msg_origin) or "").strip()
        except Exception:
            logger.exception("[ARK ASA] failed to resolve current chat provider id")
            return ""

    def _build_llm_prompt(self, question: str, reference_text: str) -> str:
        sections = [
            "用户问题：",
            question.strip(),
        ]
        if reference_text.strip():
            sections.extend(
                [
                    "",
                    "插件本地资料：",
                    reference_text.strip(),
                    "",
                    "回答要求：优先使用上面的插件本地资料；如果本地资料不够，再补充通用经验并明确标注。",
                ]
            )
        else:
            sections.extend(
                [
                    "",
                    "插件本地资料：当前没有检索到直接命中的条目，可以结合通用经验回答，但请明确说明未命中本地资料。",
                ]
            )
        return "\n".join(sections).strip()
