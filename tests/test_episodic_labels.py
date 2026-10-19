"""Episodic memory search results are labelled in the server's language."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import pytest

from cogs.episodic_memory import EpisodicMemoryService

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")
CJK = re.compile(r"[぀-ヿ一-鿿]")


class _FileTranslations:
    """Resolves ("commands", "memory", ...) lookups against one locale's real memory.json."""

    def __init__(self, locale: str) -> None:
        self.locale = locale

    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        data = json.loads((ROOT / "translations" / self.locale / "commands" / "memory.json").read_text(encoding="utf-8"))
        node: Any = data
        for key in keys[2:]:
            node = node[key]
        return node.format(**kwargs) if kwargs else node


def _result(content: str, score: float | None, timestamp: float | None) -> SimpleNamespace:
    metadata = {"timestamp": timestamp} if timestamp is not None else {}
    return SimpleNamespace(content=content, score=score, metadata=metadata)


def _format(locale: str, results: List[Any]) -> str:
    cog = SimpleNamespace(_translate_text=lambda lang, guild, *keys, **kwargs: lang.translate(guild, *keys, **kwargs))
    return EpisodicMemoryService._format_search_results(cog, _FileTranslations(locale), "1", results)


def test_english_results_contain_no_chinese_text() -> None:
    text = _format("en_US", [_result("we met on friday", 0.91234, 1_700_000_000.0)])

    assert not CJK.search(text)
    assert "Content: we met on friday" in text
    assert "0.912" in text


def test_traditional_chinese_keeps_its_original_wording() -> None:
    text = _format("zh_TW", [_result("週五見面", 0.5, None)])

    assert text == "**結果 1:**\n內容：週五見面\n相似度：0.500\n"


def test_each_result_has_its_own_number() -> None:
    text = _format("en_US", [_result("a", None, None), _result("b", None, None)])

    assert "**Result 1:**" in text and "**Result 2:**" in text
    assert "Similarity" not in text


def test_only_ten_results_are_shown_and_the_rest_are_counted() -> None:
    text = _format("en_US", [_result(f"item {number}", None, None) for number in range(13)])

    assert "item 9" in text and "item 10" not in text
    assert text.rstrip().endswith("3 more results")


@pytest.mark.parametrize("locale", LOCALES)
def test_every_language_has_the_result_labels(locale: str) -> None:
    search = json.loads((ROOT / "translations" / locale / "commands" / "memory.json").read_text(encoding="utf-8"))["search"]

    for key in ("result_header", "result_content", "result_score", "result_time", "more_results"):
        assert search[key].strip()
