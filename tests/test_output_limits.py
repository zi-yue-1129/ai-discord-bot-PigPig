"""Long replies are split for Discord, schedule headers show the weekday and memory clearing asks first."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from addons.discord_text import reply_in_chunks, split_for_discord
from cogs.schedule import ScheduleManager
from cogs.userdata import ClearMemoryConfirmView, UserDataCog

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")


# ------------------------------------------------------------------ splitting


def test_short_text_is_not_split() -> None:
    assert split_for_discord("hello", limit=20) == ["hello"]


def test_empty_text_gives_one_empty_chunk() -> None:
    assert split_for_discord("", limit=20) == [""]


def test_text_is_split_on_line_boundaries_within_the_limit() -> None:
    text = "\n".join(f"line {number:02d}" for number in range(10))

    chunks = split_for_discord(text, limit=30)

    assert all(len(chunk) <= 30 for chunk in chunks)
    assert len(chunks) > 1
    assert "\n".join(chunks) == text


def test_a_single_line_longer_than_the_limit_is_cut() -> None:
    chunks = split_for_discord("x" * 50, limit=20)

    assert [len(chunk) for chunk in chunks] == [20, 20, 10]
    assert "".join(chunks) == "x" * 50


class _Followup:
    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []

    async def send(self, content: str, **kwargs: Any) -> None:
        self.sent.append({"content": content, **kwargs})


class _Interaction:
    def __init__(self, user_id: int = 1) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.guild_id = 5
        self.edits: List[Dict[str, Any]] = []
        self.followup = _Followup()
        self.response = _Response()

    async def edit_original_response(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)


class _Response:
    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []
        self.edited: List[Dict[str, Any]] = []

    async def send_message(self, content: str = "", **kwargs: Any) -> None:
        self.sent.append({"content": content, **kwargs})

    async def edit_message(self, **kwargs: Any) -> None:
        self.edited.append(kwargs)


@pytest.mark.asyncio
async def test_a_long_reply_is_edited_in_then_followed_up() -> None:
    interaction = _Interaction()
    text = "\n".join("y" * 900 for _ in range(5))

    await reply_in_chunks(interaction, text, ephemeral=True)

    assert len(interaction.edits) == 1 and len(interaction.edits[0]["content"]) <= 1900
    assert interaction.followup.sent and all(item["ephemeral"] is True for item in interaction.followup.sent)
    sent = [interaction.edits[0]["content"]] + [item["content"] for item in interaction.followup.sent]
    assert "\n".join(sent) == text


@pytest.mark.asyncio
async def test_a_short_reply_is_only_edited_in() -> None:
    interaction = _Interaction()

    await reply_in_chunks(interaction, "short")

    assert interaction.edits == [{"content": "short"}]
    assert interaction.followup.sent == []


# ----------------------------------------------------------------- schedule


class _FileTranslations:
    """Resolves translate() calls against the real translation files of one locale."""

    def __init__(self, locale: str) -> None:
        self.locale = locale

    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        for split in range(len(keys), 0, -1):
            path = ROOT / "translations" / self.locale / Path(*keys[:split]).with_suffix(".json")
            if path.exists():
                node: Any = json.loads(path.read_text(encoding="utf-8"))
                # Files may repeat their own name as the root key.
                if isinstance(node, dict) and keys[split - 1] in node and len(keys) > split:
                    node = node[keys[split - 1]]
                for key in keys[split:]:
                    if not isinstance(node, dict) or key not in node:
                        return f"[Translation not found: {'.'.join(keys)}]"
                    node = node[key]
                return str(node).format(**kwargs) if isinstance(node, str) and kwargs else str(node)
        return f"[Translation not found: {'.'.join(keys)}]"


@pytest.mark.parametrize("locale", LOCALES)
def test_the_full_schedule_names_each_weekday(locale: str) -> None:
    cog = SimpleNamespace(lang_manager=_FileTranslations(locale))
    schedule = {"Monday": [{"time": "09:00-10:00", "description": "class"}], "Sunday": []}

    text = ScheduleManager.format_full_schedule(cog, schedule, "1")

    assert "Translation not found" not in text
    weekdays = _FileTranslations(locale).translate("1", "commands", "schedule", "query_schedule", "choices", "weekdays", "Monday")
    assert weekdays in text and "Translation not found" not in weekdays


# -------------------------------------------------------------- memory clear


def _fake_cog(cleared: List[str]) -> SimpleNamespace:
    async def manage_user_data(**kwargs: Any) -> str:
        cleared.append(kwargs["action"])
        return "cleared"

    return SimpleNamespace(
        lang_manager=object(),
        _translate=lambda guild_id, *path, **kwargs: "/".join(path),
        manage_user_data=manage_user_data,
    )


@pytest.mark.asyncio
async def test_clearing_memory_asks_before_deleting() -> None:
    cleared: List[str] = []
    interaction = _Interaction()

    await UserDataCog.memory_clear.callback(_fake_cog(cleared), interaction)

    assert cleared == []
    prompt = interaction.response.sent[0]
    assert prompt["ephemeral"] is True and isinstance(prompt["view"], ClearMemoryConfirmView)


@pytest.mark.asyncio
async def test_confirming_clears_the_memory() -> None:
    cleared: List[str] = []
    interaction = _Interaction()
    view = ClearMemoryConfirmView(_fake_cog(cleared), user_id=1, guild_id="5")

    await view.confirm.callback(interaction)

    assert cleared == ["clear"]
    assert interaction.edits[-1]["content"] == "cleared"


@pytest.mark.asyncio
async def test_cancelling_keeps_the_memory() -> None:
    cleared: List[str] = []
    interaction = _Interaction()
    view = ClearMemoryConfirmView(_fake_cog(cleared), user_id=1, guild_id="5")

    await view.cancel.callback(interaction)

    assert cleared == []
    assert interaction.response.edited[-1]["view"] is None


@pytest.mark.asyncio
async def test_only_the_asking_user_can_confirm() -> None:
    view = ClearMemoryConfirmView(_fake_cog([]), user_id=1, guild_id="5")
    stranger = _Interaction(user_id=2)

    assert await view.interaction_check(stranger) is False
    assert stranger.response.sent[0]["ephemeral"] is True
    assert await view.interaction_check(_Interaction(user_id=1)) is True


@pytest.mark.parametrize("locale", LOCALES)
def test_the_clear_confirmation_texts_exist_in_every_language(locale: str) -> None:
    responses = json.loads((ROOT / "translations" / locale / "commands" / "userdata.json").read_text(encoding="utf-8"))["userdata"]["responses"]

    for key in ("clear_confirm", "clear_confirm_button", "clear_cancel_button", "clear_cancelled"):
        assert responses[key].strip()
