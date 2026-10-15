"""The queue button is a switch: while on, every player interface carries the queue; pressing again hides it."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import discord
import pytest
from music_cog.helpers import GUILD_ID, FakeMessage, make_interaction, make_song

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.ui_manager import UIManager

QUEUE_FIELD = "system.music.player.queue"


class _EditableMessage(FakeMessage):
    """A channel message that also records edits."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.edits: List[dict] = []

    async def edit(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)


class _Channel:
    def __init__(self) -> None:
        self.sent: List[_EditableMessage] = []

    async def send(self, **kwargs: Any) -> _EditableMessage:
        message = _EditableMessage(**kwargs)
        self.sent.append(message)
        return message


class _Thumbnails:
    def get_thumbnail_url(self, video_id: str) -> str:
        return f"https://example.invalid/{video_id}.jpg"


@pytest.fixture
def channel() -> _Channel:
    return _Channel()


@pytest.fixture
def player(
    cog: YTMusic, guild: SimpleNamespace, requester: SimpleNamespace, channel: _Channel
) -> PlaybackContext:
    """A context posting into a channel whose messages can be edited, with the real UI manager in the cog."""
    manager = UIManager(bot=None)
    manager.lang_manager = cog.lang_manager
    cog.ui_manager = manager
    return PlaybackContext(guild=guild, channel=channel, user=requester)


async def _post(cog: YTMusic, ctx: PlaybackContext, index: int = 1) -> _EditableMessage:
    song = make_song(index) | {"requester": ctx.user, "user_avatar": "https://example.invalid/a.png"}
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    return await cog.ui_manager.update_player_ui(ctx, song, None, _Thumbnails(), cog)


def _queue_fields(cog: YTMusic) -> List[discord.embeds.EmbedProxy]:
    embed = cog.ui_manager.get_current_view(GUILD_ID).current_embed
    return [field for field in embed.fields if field.name == QUEUE_FIELD]


def _press(cog: YTMusic, ctx: PlaybackContext) -> Any:
    return cog.handle_show_queue(make_interaction(ctx.guild, ctx.channel, ctx.user))


def _queue_button(cog: YTMusic) -> discord.ui.Button:
    view = cog.ui_manager.get_current_view(GUILD_ID)
    return next(child for child in view.children if getattr(child, "custom_id", None) == "show_queue")


@pytest.mark.asyncio
async def test_the_first_press_shows_the_queue_and_the_second_hides_it(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)

    await _press(cog, player)
    assert len(_queue_fields(cog)) == 1
    assert cog.state_manager.get_state(GUILD_ID).show_queue is True

    await _press(cog, player)
    assert _queue_fields(cog) == []
    assert cog.state_manager.get_state(GUILD_ID).show_queue is False


@pytest.mark.asyncio
async def test_the_queue_button_is_lit_while_the_queue_is_shown(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)
    assert _queue_button(cog).style == discord.ButtonStyle.gray

    await _press(cog, player)
    assert _queue_button(cog).style == discord.ButtonStyle.green

    await _press(cog, player)
    assert _queue_button(cog).style == discord.ButtonStyle.gray


@pytest.mark.asyncio
async def test_the_next_song_keeps_showing_the_queue_without_another_press(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player, 1)
    await _press(cog, player)

    await _post(cog, player, 2)

    assert len(_queue_fields(cog)) == 1


@pytest.mark.asyncio
async def test_the_next_song_has_no_queue_after_it_was_hidden(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player, 1)
    await _press(cog, player)
    await _press(cog, player)

    await _post(cog, player, 2)

    assert _queue_fields(cog) == []


@pytest.mark.asyncio
async def test_the_shown_queue_follows_songs_added_later(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)
    await _press(cog, player)
    assert "song 7" not in _queue_fields(cog)[0].value

    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(7))
    refreshed = await cog.ui_manager.get_current_view(GUILD_ID).refresh_queue_field()

    assert refreshed is True
    assert "song 7" in _queue_fields(cog)[0].value


@pytest.mark.asyncio
async def test_nothing_is_refreshed_while_the_queue_is_hidden(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)

    assert await cog.ui_manager.get_current_view(GUILD_ID).refresh_queue_field() is False
    assert _queue_fields(cog) == []


# ------------------------------------------------------------ queue size


class _Texts:
    """Returns each text's dotted path, except the queue total, which keeps its count."""

    def translate(self, guild_id: str, *path: str, **kwargs: Any) -> str:
        if path[-1] == "queue_total":
            return f"total={kwargs['count']}"
        return ".".join(path)


async def _queue_text(cog: YTMusic, queued: int, *, playing: bool) -> str:
    cog.lang_manager = _Texts()
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0) if playing else None)
    for index in range(1, queued + 1):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))
    return await cog.get_queue_text(GUILD_ID)


@pytest.mark.asyncio
async def test_the_queue_list_says_how_many_songs_are_queued(cog: YTMusic) -> None:
    text = await _queue_text(cog, 3, playing=True)

    assert "total=3" in text


@pytest.mark.asyncio
async def test_the_queue_list_says_zero_when_only_the_current_song_is_left(cog: YTMusic) -> None:
    text = await _queue_text(cog, 0, playing=True)

    assert "total=0" in text


@pytest.mark.asyncio
async def test_an_idle_player_with_an_empty_queue_still_shows_the_empty_notice(cog: YTMusic) -> None:
    text = await _queue_text(cog, 0, playing=False)

    assert text == "system.music.player.queue_empty"


@pytest.mark.parametrize("locale", ("zh_TW", "zh_CN", "en_US", "ja_JP"))
def test_the_queue_total_is_translated(locale: str) -> None:
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "translations" / locale / "system" / "music" / "controls.json"

    assert "{count}" in json.loads(path.read_text(encoding="utf-8"))["queue_total"]
