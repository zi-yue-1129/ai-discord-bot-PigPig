"""Progress messages: every tool has a status text and a model switch is shown to the user."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, List

import pytest

from llm.utils import progress
from llm.utils.progress import announce_model_switch

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")


def _tool_names() -> set:
    """Names of every function decorated with ``@tool`` under llm/."""
    names = set()
    for path in (ROOT / "llm").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    target = decorator.func if isinstance(decorator, ast.Call) else decorator
                    if getattr(target, "id", getattr(target, "attr", "")) == "tool":
                        names.add(node.name)
    return names


def _responses(locale: str) -> dict:
    path = ROOT / "translations" / locale / "system" / "chat_bot.json"
    return json.loads(path.read_text(encoding="utf-8"))["responses"]


@pytest.mark.parametrize("locale", LOCALES)
def test_every_tool_has_a_status_text(locale: str) -> None:
    missing = _tool_names() - set(_responses(locale)["tools"])

    assert missing == set()


@pytest.mark.parametrize("locale", LOCALES)
def test_the_model_switch_text_exists_and_is_not_empty(locale: str) -> None:
    assert _responses(locale)["switching_model"].strip()


class _Language:
    """Language manager stand-in returning a fixed text and recording the lookups."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.lookups: List[tuple] = []

    def translate(self, guild_id: str, *path: str, **kwargs: Any) -> str:
        self.lookups.append((guild_id, path))
        return self.text


@pytest.fixture
def edits(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    sent: List[str] = []

    async def fake_edit(message: Any, content: str) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(progress, "safe_edit_message", fake_edit)
    return sent


@pytest.mark.asyncio
async def test_a_model_switch_updates_the_status_message(edits: List[str]) -> None:
    language = _Language("switching now")

    await announce_model_switch(object(), language, "7", has_next_model=True)

    assert edits == ["switching now"]
    assert language.lookups == [("7", ("system", "chat_bot", "responses", "switching_model"))]


@pytest.mark.asyncio
async def test_nothing_is_announced_when_no_model_is_left(edits: List[str]) -> None:
    await announce_model_switch(object(), _Language("switching now"), "7", has_next_model=False)

    assert edits == []


@pytest.mark.asyncio
async def test_without_a_language_manager_an_english_text_is_used(edits: List[str]) -> None:
    await announce_model_switch(object(), None, "7", has_next_model=True)

    assert len(edits) == 1 and "backup" in edits[0].lower()


@pytest.mark.asyncio
async def test_a_failed_status_edit_does_not_break_the_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_edit(message: Any, content: str) -> bool:
        raise RuntimeError("discord is down")

    monkeypatch.setattr(progress, "safe_edit_message", failing_edit)

    await announce_model_switch(object(), _Language("switching now"), "7", has_next_model=True)
