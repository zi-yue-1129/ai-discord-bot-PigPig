"""Smaller fixes from the non-music audit: command errors, summaries, DMs, templates and the eat flow."""

from __future__ import annotations

import asyncio
import sqlite3
import json
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import discord
import pytest
from discord import app_commands

from addons.command_errors import describe_command_error
from cogs import summarizer
from cogs.channel_manager import ChannelManager
from cogs.internet_search import InternetSearchCog
from cogs.language_manager import LanguageManager
from cogs.schedule import ScheduleManager
from cogs.summarizer import SummarizerCog

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")


# ------------------------------------------------------------ command errors


class _Translations:
    """Returns canned texts for the keys it knows and the real "not found" marker otherwise."""

    def __init__(self, texts: Dict[tuple, str]) -> None:
        self.texts = texts

    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        text = self.texts.get(keys)
        return text.format(**kwargs) if text is not None else f"[Translation not found: {'.'.join(keys)}]"


TEXTS = {
    ("errors", "cooldown"): "wait {retry_after}s",
    ("errors", "permission_denied"): "no permission",
    ("system", "errors", "unexpected"): "unexpected",
}


def test_a_cooldown_tells_how_long_to_wait() -> None:
    error = app_commands.CommandOnCooldown(app_commands.Cooldown(1, 5.0), 3.26)

    assert describe_command_error(error, _Translations(TEXTS), "1") == "wait 3.3s"


def test_a_failed_permission_check_is_reported_as_no_permission() -> None:
    assert describe_command_error(app_commands.CheckFailure(), _Translations(TEXTS), "1") == "no permission"


def test_missing_permissions_are_reported_as_no_permission() -> None:
    error = app_commands.MissingPermissions(["administrator"])

    assert describe_command_error(error, _Translations(TEXTS), "1") == "no permission"


def test_other_errors_are_reported_as_unexpected() -> None:
    assert describe_command_error(app_commands.AppCommandError("boom"), _Translations(TEXTS), "1") == "unexpected"


def test_a_missing_translation_never_reaches_the_user() -> None:
    text = describe_command_error(app_commands.CheckFailure(), _Translations({}), "1")

    assert "Translation not found" not in text and text


def test_without_a_language_manager_a_plain_message_is_used() -> None:
    assert describe_command_error(app_commands.CheckFailure(), None, "1")


@pytest.mark.parametrize("locale", LOCALES)
def test_every_language_has_a_cooldown_text(locale: str) -> None:
    errors = json.loads((ROOT / "translations" / locale / "errors.json").read_text(encoding="utf-8"))

    assert "{retry_after}" in errors["cooldown"]


# --------------------------------------------------------------- summarizing


class _SummaryChannel:
    name = "general"

    def __init__(self, messages: List[Any]) -> None:
        self.messages = messages
        self.limits: List[int] = []

    def history(self, limit: int) -> Any:
        self.limits.append(limit)
        messages = list(self.messages)

        async def generator() -> Any:
            for message in messages:
                yield message

        return generator()


class _SummaryInteraction:
    def __init__(self, channel: _SummaryChannel) -> None:
        self.guild_id = 1
        self.channel = channel
        self.sent: List[Dict[str, Any]] = []
        self.response = SimpleNamespace(defer=self._defer)
        self.followup = SimpleNamespace(send=self._send)

    async def _defer(self, **kwargs: Any) -> None:
        return None

    async def _send(self, content: Optional[str] = None, **kwargs: Any) -> None:
        self.sent.append({"content": content, **kwargs})


def _human_message(text: str, author_id: int = 5) -> SimpleNamespace:
    from datetime import datetime

    return SimpleNamespace(
        content=text, created_at=datetime(2026, 1, 1, 9, 0), jump_url="https://discord.com/x",
        author=SimpleNamespace(bot=False, display_name="Al", id=author_id),
    )


def _summarizer(hidden: Any = frozenset(), broken: bool = False) -> SimpleNamespace:
    """A stand-in cog whose server has ``hidden`` members (/leaderboard optout); ``broken``: the list cannot be read."""

    def optouts(guild_id: int) -> Any:
        if broken:
            raise sqlite3.OperationalError("database is locked")
        return set(hidden)

    cogs = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(optouts=optouts))}
    return SimpleNamespace(
        MAX_CHAR_COUNT=15000, EMBED_DESC_LIMIT=4000, lang_manager=None, bot=SimpleNamespace(get_cog=cogs.get)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("asked, searched", [(10**6, summarizer.MAX_SUMMARY_MESSAGES), (-5, 1), (100, 100)])
async def test_the_number_of_messages_searched_is_bounded(asked: int, searched: int) -> None:
    channel = _SummaryChannel([])

    await SummarizerCog.summarize.callback(_summarizer(), _SummaryInteraction(channel), limit=asked)

    assert channel.limits == [searched]


@pytest.mark.asyncio
async def test_a_slow_model_gives_a_timeout_message_without_internal_details(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    class _Agent:
        async def ainvoke(self, state: Any) -> Any:
            while not release.is_set():
                await asyncio.sleep(0.01)
            return {"messages": [SimpleNamespace(content="late")]}

    async def no_report(error: Exception, details: str = "") -> None:
        return None

    monkeypatch.setattr(summarizer, "SUMMARY_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(summarizer, "ModelManager", lambda: SimpleNamespace(get_model=lambda *a, **k: ("m", None)))
    monkeypatch.setattr(summarizer, "create_model_instance", lambda *a, **k: object())
    monkeypatch.setattr(summarizer, "create_agent", lambda **k: _Agent())
    monkeypatch.setattr(summarizer.func, "report_error", no_report)
    interaction = _SummaryInteraction(_SummaryChannel([_human_message("hello there")]))

    await asyncio.wait_for(SummarizerCog.summarize.callback(_summarizer(), interaction, limit=10), timeout=3)
    release.set()

    assert len(interaction.sent) == 1 and interaction.sent[0]["ephemeral"] is True
    assert "timed out" in interaction.sent[0]["content"].lower()


@pytest.mark.asyncio
async def test_an_unexpected_failure_does_not_show_the_exception_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Agent:
        async def ainvoke(self, state: Any) -> Any:
            raise RuntimeError("http://10.0.0.5:8000/secret-backend failed")

    async def no_report(error: Exception, details: str = "") -> None:
        return None

    monkeypatch.setattr(summarizer, "ModelManager", lambda: SimpleNamespace(get_model=lambda *a, **k: ("m", None)))
    monkeypatch.setattr(summarizer, "create_model_instance", lambda *a, **k: object())
    monkeypatch.setattr(summarizer, "create_agent", lambda **k: _Agent())
    monkeypatch.setattr(summarizer.func, "report_error", no_report)
    interaction = _SummaryInteraction(_SummaryChannel([_human_message("hello there")]))

    await SummarizerCog.summarize.callback(_summarizer(), interaction, limit=10)

    assert "10.0.0.5" not in interaction.sent[0]["content"]


def _recording_model(monkeypatch: pytest.MonkeyPatch) -> List[Any]:
    """Replaces the summary model by one that records what it was given; returns that record."""
    given: List[Any] = []

    class _Agent:
        async def ainvoke(self, state: Any) -> Any:
            given.extend(state["messages"])
            return {"messages": [SimpleNamespace(content="a summary")]}

    monkeypatch.setattr(summarizer, "ModelManager", lambda: SimpleNamespace(get_model=lambda *a, **k: ("m", None)))
    monkeypatch.setattr(summarizer, "create_model_instance", lambda *a, **k: object())
    monkeypatch.setattr(summarizer, "create_agent", lambda **k: _Agent())
    return given


@pytest.mark.asyncio
async def test_a_hidden_members_messages_are_not_summarized(monkeypatch: pytest.MonkeyPatch) -> None:
    given = _recording_model(monkeypatch)
    channel = _SummaryChannel([_human_message("what a visible person said", 5), _human_message("what a hidden person said", 11)])

    await SummarizerCog.summarize.callback(_summarizer(hidden={11}), _SummaryInteraction(channel), limit=10)

    texts = " ".join(str(message.content) for message in given)
    assert "visible person" in texts and "hidden person" not in texts


@pytest.mark.asyncio
async def test_nothing_is_summarized_while_the_opt_out_list_cannot_be_read(monkeypatch: pytest.MonkeyPatch) -> None:
    given = _recording_model(monkeypatch)
    interaction = _SummaryInteraction(_SummaryChannel([_human_message("anything at all", 5)]))

    await SummarizerCog.summarize.callback(_summarizer(broken=True), interaction, limit=10)

    assert given == [] and interaction.sent[0]["content"] == "No messages to summarize."


# ----------------------------------------------------------- direct messages


def test_server_only_commands_are_not_offered_in_direct_messages() -> None:
    commands = list(ChannelManager.__cog_app_commands__) + [LanguageManager.set_language, ScheduleManager.query_schedule_command]

    assert commands and all(command.guild_only for command in commands)


@pytest.mark.asyncio
async def test_a_failed_config_save_is_not_hidden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reports: List[str] = []

    async def record_report(error: Exception, details: str = "") -> None:
        reports.append(details)

    monkeypatch.setattr("cogs.channel_manager.func.report_error", record_report)
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where a folder is needed", encoding="utf-8")
    cog = SimpleNamespace(get_config_path=lambda guild_id: str(blocker / "config.json"))

    with pytest.raises(NotADirectoryError, match="blocker"):
        ChannelManager.save_config(cog, "1", {"mode": "unrestricted"})
    await asyncio.sleep(0)

    assert reports == ["saving config for guild 1"]


# ------------------------------------------------------------------ schedule


class _ScheduleLanguage:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return "/".join(keys)


@pytest.mark.asyncio
async def test_querying_someone_who_left_the_server_gives_a_clear_answer(tmp_path: Path) -> None:
    (tmp_path / "9.yaml").write_text("channel_id: 5\nschedule: {}\n", encoding="utf-8")

    async def fetch_member(user_id: int) -> Any:
        raise discord.NotFound(SimpleNamespace(status=404, reason="gone"), "Unknown Member")

    guild = SimpleNamespace(id=1, fetch_member=fetch_member)
    interaction = SimpleNamespace(guild_id=1, guild=guild, user=SimpleNamespace(id=2), channel_id=5)
    cog = SimpleNamespace(
        schedule_dir=str(tmp_path), lang_manager=_ScheduleLanguage(),
        _sanitize_schedule_data=lambda data, channel_id: (data or {"schedule": {}, "channel_id": 5}, False),
    )

    result = await ScheduleManager._core_query_schedule(cog, interaction, "full", 9)

    assert result == "commands/query_schedule/responses/user_not_found"


@pytest.mark.asyncio
async def test_a_long_template_is_sent_as_a_binary_file(tmp_path: Path) -> None:
    (tmp_path / "template.yaml").write_text("key: value\n" * 400, encoding="utf-8")
    sent: List[Dict[str, Any]] = []

    async def send_message(content: str = "", **kwargs: Any) -> None:
        sent.append({"content": content, **kwargs})

    interaction = SimpleNamespace(guild_id=1, response=SimpleNamespace(send_message=send_message))
    cog = SimpleNamespace(schedule_dir=str(tmp_path), lang_manager=None)

    await ScheduleManager.show_template_command.callback(cog, interaction)

    attachment = sent[0]["file"]
    assert isinstance(attachment.fp.read(), bytes)


# ------------------------------------------------------------------ eat flow


class _LoadingMessage:
    def __init__(self) -> None:
        self.edits: List[Dict[str, Any]] = []
        self.deleted = False

    async def edit(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)

    async def delete(self) -> None:
        self.deleted = True


@pytest.mark.asyncio
async def test_a_failed_eat_search_does_not_leave_the_loading_card_behind(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Provider:
        async def search(self, keyword: str, lang: str) -> List[dict]:
            return []

    cog = SimpleNamespace(
        lang_manager=None, provider=_Provider(), db=SimpleNamespace(checkKeyword=lambda keyword: True),
        _remove_loading=lambda message: InternetSearchCog._remove_loading(cog, message),
    )
    loading = _LoadingMessage()

    result = await InternetSearchCog.eat_search(cog, SimpleNamespace(guild=None), "ramen", loading)

    assert result and "ramen" in result
    assert loading.deleted is True
