from __future__ import annotations

from pathlib import Path
from typing import Callable

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.config.astrbot_config import AstrBotConfig

from .services.query_service import ArkQueryService, QueryResult


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
        self.service = ArkQueryService(
            plugin_dir=Path(__file__).resolve().parent,
            max_suggestions=int(_safe_config_get(config, "max_suggestions", 3)),
            show_source_url=bool(_safe_config_get(config, "show_source_url", True)),
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

    async def _dispatch_ark(self, event: AstrMessageEvent):
        raw = (event.message_str or "").strip()
        parts = raw.split(maxsplit=2)

        if len(parts) == 1:
            yield event.plain_result(self.service.help_text())
            return

        subcommand = parts[1].strip().lower()
        argument = parts[2].strip() if len(parts) > 2 else ""

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
            "map": self.service.query_map_resource,
            "地图": self.service.query_map_resource,
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
            result = self.service.query_map_resource(argument)
        else:
            result = self.service.help_result()

        yield event.plain_result(result.message)
