"""Localizes slash command descriptions, parameter descriptions and choice names.

Commands are declared in English. Discord shows each user the text for their
own client language, read from ``translations/<lang>/slash_commands.json``:
a flat map from the English text to its translation. Command and parameter
names are left as they are so that they stay the same for everyone.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

import discord
from discord import app_commands

from addons.logging import get_logger

log = get_logger(server_id="Bot", source=__name__)

# Bot language folder -> the Discord client languages that use it.
LOCALE_FOLDERS: Dict[discord.Locale, str] = {
    discord.Locale.taiwan_chinese: "zh_TW",
    discord.Locale.chinese: "zh_CN",
    discord.Locale.japanese: "ja_JP",
}

# Strings Discord lets us localize; names are not, so commands keep one name.
_LOCALIZED = {
    app_commands.TranslationContextLocation.command_description,
    app_commands.TranslationContextLocation.group_description,
    app_commands.TranslationContextLocation.parameter_description,
    app_commands.TranslationContextLocation.choice_name,
}


def load_tables(translations_dir: str) -> Dict[str, Dict[str, str]]:
    """Reads each language's slash_commands.json; a missing or broken file means no translations for it."""
    tables: Dict[str, Dict[str, str]] = {}
    for folder in set(LOCALE_FOLDERS.values()):
        path = os.path.join(translations_dir, folder, "slash_commands.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tables[folder] = {str(k): str(v) for k, v in data.items() if v}
        except FileNotFoundError:
            tables[folder] = {}
        except (OSError, ValueError):
            log.warning(f"Could not read {path}; slash commands stay in English for {folder}")
            tables[folder] = {}
    return tables


class CommandTranslator(app_commands.Translator):
    """Serves slash command text from the per-language tables."""

    def __init__(self, translations_dir: str) -> None:
        self.tables = load_tables(translations_dir)

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> Optional[str]:
        if context.location not in _LOCALIZED:
            return None
        folder = LOCALE_FOLDERS.get(locale)
        if folder is None:
            return None
        text = self.tables.get(folder, {}).get(string.message)
        if not text:
            return None
        # Discord's limits: 100 characters for descriptions and choice names.
        return text[:100]
