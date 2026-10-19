"""The player interface that is re-posted on every song change must not ring everyone's phone."""

from __future__ import annotations

from typing import Any

import pytest
from music_cog.helpers import GUILD_ID, FakeChannel, make_song

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.ui_manager import UIManager


@pytest.fixture
def real_ui(cog: YTMusic) -> UIManager:
    """The real UI manager, with the fake language manager of the cog."""
    manager = UIManager(bot=None)
    manager.lang_manager = cog.lang_manager
    return manager


class _Thumbnails:
    """Stands in for the YouTube manager, which only supplies thumbnail URLs to the embed."""

    def get_thumbnail_url(self, video_id: str) -> str:
        return f"https://example.invalid/{video_id}.jpg"


def _post(real_ui: UIManager, cog: YTMusic, ctx: PlaybackContext, song: dict, previous: Any = None) -> Any:
    song = song | {"requester": ctx.user, "user_avatar": "https://example.invalid/a.png"}
    return real_ui.update_player_ui(ctx, song, previous, _Thumbnails(), cog)


@pytest.mark.asyncio
async def test_the_player_interface_is_sent_without_a_notification(
    cog: YTMusic, ctx: PlaybackContext, text_channel: FakeChannel, real_ui: UIManager
) -> None:
    message = await _post(real_ui, cog, ctx, make_song(1))

    assert message is text_channel.sent[-1]
    assert message.kwargs["silent"] is True
    assert message.kwargs["view"] is real_ui.views[GUILD_ID]


@pytest.mark.asyncio
async def test_the_previous_interface_is_still_removed_when_the_next_one_is_posted(
    cog: YTMusic, ctx: PlaybackContext, text_channel: FakeChannel, real_ui: UIManager
) -> None:
    first = await _post(real_ui, cog, ctx, make_song(1))

    second = await _post(real_ui, cog, ctx, make_song(2), first)

    assert first.deleted
    assert second is text_channel.sent[-1]
    assert cog.state_manager.get_state(GUILD_ID).ui_messages == [second]
