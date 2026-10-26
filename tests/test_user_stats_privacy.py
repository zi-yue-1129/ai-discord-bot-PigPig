"""The AI stats tool must not reveal hidden members or what was said in private channels."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Optional

import pytest

from llm.tools.user_stats import UserStatsTools

GUILD_ID = 42
AUTHOR_ID = 10
HIDDEN_ID = 11

STATS = {
    "total_messages": 50,
    "streak_days": 2,
    "active_hours": {"12": 50},
    "top_words": {"secretproject": 40},
    "top_emojis": {"🤫": 9},
    "top_channels": {"500": 10, "666": 40},
}


class FakeStorage:
    def __init__(self) -> None:
        self.asked: list = []

    async def get_user_stats(self, user_id: str, guild_id: str) -> Optional[dict]:
        self.asked.append(user_id)
        return dict(STATS)


class FakeOptouts:
    def is_opted_out(self, guild_id: int, user_id: int) -> bool:
        return guild_id == GUILD_ID and user_id == HIDDEN_ID


def _channel(channel_id: int, public: bool) -> Any:
    return SimpleNamespace(
        id=channel_id,
        overwrites={},
        permissions_for=lambda role: SimpleNamespace(view_channel=public, read_message_history=public),
    )


class FakeChannel:
    def __init__(self) -> None:
        self.files: list = []

    async def send(self, file: Any = None, **kwargs: Any) -> None:
        self.files.append(file)


def _tool(storage: FakeStorage) -> Any:
    guild = SimpleNamespace(
        id=GUILD_ID,
        default_role="@everyone",
        channels=[_channel(500, True), _channel(666, False)],
        get_member=lambda member_id: None,
    )
    for channel in guild.channels:
        channel.guild = guild
    message = SimpleNamespace(guild=guild, author=SimpleNamespace(id=AUTHOR_ID), channel=FakeChannel())
    cogs = {"StatsCog": SimpleNamespace(stats_storage=storage), "LeaderboardCog": SimpleNamespace(store=FakeOptouts())}
    runtime = SimpleNamespace(bot=SimpleNamespace(get_cog=cogs.get), message=message, logger=None)
    return UserStatsTools(runtime).get_tools()[0].coroutine


@pytest.mark.asyncio
async def test_a_hidden_member_cannot_be_looked_up() -> None:
    storage = FakeStorage()

    reply = await _tool(storage)(user_id=str(HIDDEN_ID))

    assert "hide" in reply and storage.asked == []


@pytest.mark.asyncio
async def test_words_emojis_and_private_channels_are_left_out(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list = []

    def fake_image(name: str, stats: dict, avatar: Any, labels: dict) -> bytes:
        seen.append(stats)
        return b"png"

    monkeypatch.setattr("llm.tools.user_stats._generate_stats_image_sync", fake_image)

    reply = await _tool(FakeStorage())(user_id=str(AUTHOR_ID))

    assert "secretproject" not in reply and "🤫" not in reply and "666" not in reply
    assert seen[0]["top_words"] == {} and seen[0]["top_channels"] == {"500": 10}


def test_the_opt_out_list_fails_closed() -> None:
    from llm.tools.user_stats import _is_hidden

    class Broken:
        def is_opted_out(self, guild_id: int, user_id: int) -> bool:
            raise RuntimeError("database is locked")

    runtime = SimpleNamespace(bot=SimpleNamespace(get_cog=lambda name: SimpleNamespace(store=Broken())))
    assert _is_hidden(runtime, GUILD_ID, str(AUTHOR_ID)) is True


def test_without_the_leaderboard_cog_the_stored_opt_outs_are_read(tmp_path: Any) -> None:
    from cogs.community_lib.store import CommunityStore
    from llm.tools.user_stats import _is_hidden

    path = str(tmp_path / "community.db")
    CommunityStore(path).set_optout(GUILD_ID, HIDDEN_ID, True)
    runtime = SimpleNamespace(bot=SimpleNamespace(get_cog=lambda name: None))

    assert _is_hidden(runtime, GUILD_ID, str(HIDDEN_ID), db_path=path) is True
    assert _is_hidden(runtime, GUILD_ID, str(AUTHOR_ID), db_path=path) is False


@pytest.mark.asyncio
async def test_a_malformed_user_id_is_refused() -> None:
    storage = FakeStorage()

    reply = await _tool(storage)(user_id="abc")

    assert "not a Discord user ID" in reply and storage.asked == []


def test_all_time_words_stay_hidden_even_when_every_channel_is_public() -> None:
    from llm.tools.user_stats import public_stats

    guild = SimpleNamespace(default_role="@everyone", channels=[_channel(500, True)], threads=[])
    guild.channels[0].guild = guild
    stats = {"total_messages": 10, "top_channels": {"500": 10}, "top_words": {"pizza": 3}, "top_emojis": {"😂": 2}}

    shown = public_stats(guild, stats, also_visible=500)

    # They record neither the channel nor whether it was public when written.
    assert shown["top_words"] == {} and shown["top_emojis"] == {}
    assert shown["top_channels"] == {"500": 10}


def test_public_channels_follow_the_real_discord_permission_rules() -> None:
    import discord

    from cogs.community_lib.recap import is_public, public_channel_ids
    from test_visibility import _guild, _member, _overwrite, _private_thread, _role

    open_guild = _guild()
    assert public_channel_ids(open_guild) == ["10"]

    denied = _guild(
        roles=[_role(2, discord.Permissions.none(), 1)],
        members=[_member(5, [2]), _member(6)],
        overwrites=[_overwrite(2, 0, deny=discord.Permissions(view_channel=True))],
    )
    assert public_channel_ids(denied) == []

    thread = _private_thread(open_guild, owner=5, members=[5])
    assert is_public(open_guild, thread) is False


@pytest.mark.asyncio
async def test_words_counted_while_public_are_shown_for_channels_still_public() -> None:
    from llm.tools.user_stats import with_public_terms

    class Storage:
        def __init__(self) -> None:
            self.asked: list = []

        async def get_user_public_terms(self, user_id: str, guild_id: str, kind: str, channel_ids: Any, limit: int) -> list:
            self.asked.append(sorted(channel_ids))
            return [("pizza", 3)] if kind == "word" else [("😀", 1)]

    guild = SimpleNamespace(id=GUILD_ID, default_role="@everyone", channels=[_channel(500, True), _channel(666, False)], threads=[])
    for channel in guild.channels:
        channel.guild = guild
    storage = Storage()
    stats = {"total_messages": 5, "top_channels": {"500": 5}, "top_words": {"secretproject": 9}, "top_emojis": {"🤫": 2}}

    shown = await with_public_terms(storage, guild, str(AUTHOR_ID), stats)

    assert shown["top_words"] == {"pizza": 3} and shown["top_emojis"] == {"😀": 1}
    assert storage.asked == [["500"], ["500"]]
