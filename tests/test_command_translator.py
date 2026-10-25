"""Slash command descriptions and choices follow the user's Discord language."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import discord
import pytest
from discord import app_commands

from addons.command_translator import CommandTranslator

ROOT = Path(__file__).resolve().parents[1]


def _context(location: app_commands.TranslationContextLocation) -> app_commands.TranslationContext:
    return app_commands.TranslationContext(location=location, data=SimpleNamespace())


@pytest.mark.asyncio
async def test_descriptions_and_choices_are_translated() -> None:
    translator = CommandTranslator(str(ROOT / "translations"))
    text = app_commands.locale_str("Sets a reminder")

    loc = app_commands.TranslationContextLocation
    assert await translator.translate(text, discord.Locale.taiwan_chinese, _context(loc.command_description)) == "設定提醒"
    assert await translator.translate(text, discord.Locale.japanese, _context(loc.command_description)) == "リマインダーを設定"
    assert await translator.translate(app_commands.locale_str("Every day"), discord.Locale.chinese, _context(loc.choice_name)) == "每天"


@pytest.mark.asyncio
async def test_names_and_other_languages_stay_as_declared() -> None:
    translator = CommandTranslator(str(ROOT / "translations"))
    loc = app_commands.TranslationContextLocation

    assert await translator.translate(app_commands.locale_str("Sets a reminder"), discord.Locale.american_english, _context(loc.command_description)) is None
    assert await translator.translate(app_commands.locale_str("Off"), discord.Locale.taiwan_chinese, _context(loc.command_name)) is None


def _declared_strings() -> set[str]:
    """Every description, parameter description and choice name declared in the cogs."""
    found: set[str] = set()
    for path in (ROOT / "cogs").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = ast.unparse(node.func)
            for kw in node.keywords:
                if not (isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)):
                    continue
                if func.endswith("Choice") and kw.arg == "name":
                    found.add(kw.value.value)
                elif func.endswith(("command", "Group")) and kw.arg == "description":
                    found.add(kw.value.value)
                elif func.endswith("describe"):
                    found.add(kw.value.value)
    return found


# Language names are shown in their own language on purpose.
_UNTRANSLATED = {"繁體中文", "简体中文", "English", "日本語"}


@pytest.mark.parametrize("folder", ["zh_TW", "zh_CN", "ja_JP"])
def test_every_declared_string_has_a_translation(folder: str) -> None:
    table = json.loads((ROOT / "translations" / folder / "slash_commands.json").read_text(encoding="utf-8"))

    missing = _declared_strings() - _UNTRANSLATED - set(table)
    assert not missing, f"{folder} is missing: {sorted(missing)}"
    assert all(len(value) <= 100 for value in table.values())
