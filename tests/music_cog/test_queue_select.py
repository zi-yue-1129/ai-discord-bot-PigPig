"""The queue menu under the player: pick a queued song, then play it next or remove it (privately)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

import discord
import pytest
from music_cog.helpers import BOT_USER_ID, GUILD_ID, make_interaction, make_member, make_song
from music_cog.helpers import post_player as _post

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.queue_manager import PlayMode

ROOT = Path(__file__).resolve().parents[2]
QUEUE_MENU = "queue_song"
PLAY_NEXT = "queue_play_next"
REMOVE = "queue_remove"


def _view(cog: YTMusic) -> Any:
    return cog.ui_manager.get_current_view(GUILD_ID)


def _menu(cog: YTMusic, custom_id: str) -> discord.ui.Select:
    return next(child for child in _view(cog).children if getattr(child, "custom_id", None) == custom_id)


def _order(cog: YTMusic) -> List[str]:
    return [song["video_id"] for song in cog.queue_manager.get_queue_snapshot(GUILD_ID)]


async def _fill(cog: YTMusic, requester: Any, count: int = 3) -> None:
    for index in range(1, count + 1):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index) | {"requester": requester})


async def _pick(cog: YTMusic, ctx: PlaybackContext, video_id: str, user: Any = None) -> Any:
    """Picks a song in the queue menu; returns the private message's action view."""
    interaction = make_interaction(ctx.guild, ctx.channel, user or ctx.user)
    menu = _menu(cog, QUEUE_MENU)
    menu._values = [video_id]
    await menu.callback(interaction)
    (reply,) = interaction.response.sent
    assert reply["ephemeral"] is True
    return reply["view"]


async def _choose(cog: YTMusic, ctx: PlaybackContext, custom_id: str, video_id: str, user: Any = None) -> Any:
    actions = await _pick(cog, ctx, video_id, user)
    button = next(child for child in actions.children if child.custom_id == custom_id)
    interaction = make_interaction(ctx.guild, ctx.channel, user or ctx.user)
    await button.callback(interaction)
    return interaction


# --------------------------------------------------------------- the menus


@pytest.mark.asyncio
async def test_the_menu_lists_the_queue_in_order(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)

    menu = _menu(cog, QUEUE_MENU)
    assert [option.value for option in menu.options] == ["v1", "v2", "v3"]
    assert menu.options[0].label.startswith("1. song 1")
    assert player.user.name in menu.options[0].description
    assert not menu.disabled


@pytest.mark.asyncio
async def test_picking_a_song_offers_to_play_it_next_or_remove_it(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)

    actions = await _pick(cog, player, "v2")

    assert [child.custom_id for child in actions.children] == [PLAY_NEXT, REMOVE]
    assert _order(cog) == ["v1", "v2", "v3"]


@pytest.mark.asyncio
async def test_a_recommended_song_is_described_as_recommended(cog: YTMusic, player: PlaybackContext) -> None:
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1, added_by=BOT_USER_ID))
    await _post(cog, player)

    assert "system.music.controls.recommended" in _menu(cog, QUEUE_MENU).options[0].description


@pytest.mark.asyncio
async def test_the_menu_is_disabled_while_the_queue_is_empty(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)

    assert _menu(cog, QUEUE_MENU).disabled


@pytest.mark.asyncio
async def test_the_menus_list_at_most_25_songs(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user, 30)
    await _post(cog, player)

    assert len(_menu(cog, QUEUE_MENU).options) == 25


@pytest.mark.asyncio
async def test_a_long_title_fits_the_option_label(cog: YTMusic, player: PlaybackContext) -> None:
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1) | {"title": "x" * 300})
    await _post(cog, player)

    assert len(_menu(cog, QUEUE_MENU).options[0].label) <= 100


@pytest.mark.asyncio
async def test_the_menus_follow_queue_changes(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)
    await _fill(cog, player.user, 2)

    await _view(cog).update_button_state()

    assert [option.value for option in _menu(cog, QUEUE_MENU).options] == ["v1", "v2"]
    assert not _menu(cog, QUEUE_MENU).disabled


# ------------------------------------------------------------- choosing


@pytest.mark.asyncio
async def test_choosing_a_song_to_play_next_moves_it_to_the_front(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)

    await _choose(cog, player, PLAY_NEXT, "v3")

    assert _order(cog) == ["v3", "v1", "v2"]
    assert _view(cog).current_embed.title == "system.music.controls.queue_played_next"
    assert [option.value for option in _menu(cog, QUEUE_MENU).options] == ["v3", "v1", "v2"]


@pytest.mark.asyncio
async def test_choosing_a_song_to_remove_takes_it_out_of_the_queue(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)

    await _choose(cog, player, REMOVE, "v2")

    assert _order(cog) == ["v1", "v3"]
    assert _view(cog).current_embed.title == "system.music.controls.queue_removed"
    assert [option.value for option in _menu(cog, QUEUE_MENU).options] == ["v1", "v3"]


@pytest.mark.asyncio
async def test_a_song_that_already_left_the_queue_is_reported(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)
    cog.queue_manager.remove_at(GUILD_ID, 1)

    interaction = await _choose(cog, player, REMOVE, "v2")

    assert _order(cog) == ["v1", "v3"]
    reply = interaction.response.sent[0]
    assert reply["ephemeral"] is True
    assert "not_in_queue" in reply["args"][0]


@pytest.mark.asyncio
async def test_someone_outside_the_voice_channel_cannot_change_the_queue(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)
    outsider = make_member(99, voice_channel=None)

    for custom_id in (PLAY_NEXT, REMOVE):
        interaction = await _choose(cog, player, custom_id, "v3", user=outsider)
        assert interaction.response.sent[0]["ephemeral"] is True

    assert _order(cog) == ["v1", "v2", "v3"]


# ------------------------------------------------------------- footer & texts


@pytest.mark.asyncio
async def test_the_footer_names_the_requester_by_server_nickname(cog: YTMusic, player: PlaybackContext) -> None:
    player.user.display_name = "暱稱"
    captured: List[dict] = []

    class _Recorder:
        def translate(self, guild_id: str, *path: str, **kwargs: Any) -> str:
            captured.append({"path": path, **kwargs})
            return ".".join(path)

    cog.ui_manager.lang_manager = _Recorder()
    await _post(cog, player)

    (added_by,) = [call for call in captured if call["path"][-1] == "added_by"]
    assert added_by["user"] == "暱稱"


@pytest.mark.parametrize("locale", ("zh_TW", "zh_CN", "en_US", "ja_JP"))
def test_the_menu_texts_are_translated(locale: str) -> None:
    controls = json.loads((ROOT / "translations" / locale / "system" / "music" / "controls.json").read_text(encoding="utf-8"))
    errors = json.loads((ROOT / "translations" / locale / "system" / "music" / "ai_errors.json").read_text(encoding="utf-8"))

    for key in ("queue_song_placeholder", "queue_play_next_action", "queue_remove_action", "queue_select_empty"):
        assert controls[key].strip()
    assert "{title}" in controls["queue_played_next"] and "{user}" in controls["queue_played_next"]
    assert "{title}" in controls["queue_removed"] and "{user}" in controls["queue_removed"]
    assert errors["not_in_queue"].strip()



@pytest.mark.asyncio
async def test_the_player_has_two_rows_of_buttons_and_three_menus(cog: YTMusic, player: PlaybackContext) -> None:
    await _fill(cog, player.user)
    await _post(cog, player)

    rows = _view(cog).to_components()

    assert [len(row["components"]) for row in rows] == [5, 5, 1, 1, 1]
    assert [rows[index]["components"][0]["custom_id"] for index in (2, 3, 4)] == [QUEUE_MENU, "play_mode", "audio_filter"]
    assert [button["custom_id"] for button in rows[0]["components"]] == [
        "previous", "toggle_playback", "skip", "stop", "toggle_lyrics"
    ]
    assert [button["custom_id"] for button in rows[1]["components"]] == [
        "toggle_shuffle", "show_queue", "toggle_autoplay", "seek_back", "seek_forward"
    ]


@pytest.mark.asyncio
async def test_the_mode_and_effect_menus_show_the_current_setting(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    cog.state_manager.get_state(GUILD_ID).audio_filter = "nightcore"

    await _view(cog).update_button_state()

    assert [option.value for option in _menu(cog, "play_mode").options if option.default] == ["loop_queue"]
    assert [option.value for option in _menu(cog, "audio_filter").options if option.default] == ["nightcore"]


@pytest.mark.asyncio
async def test_choosing_a_mode_in_the_menu_sets_it(cog: YTMusic, player: PlaybackContext) -> None:
    await _post(cog, player)
    interaction = make_interaction(player.guild, player.channel, player.user)
    menu = _menu(cog, "play_mode")
    menu._values = ["loop_single"]

    await menu.callback(interaction)

    assert cog.queue_manager.get_play_mode(GUILD_ID) == PlayMode.LOOP_SINGLE
    assert _view(cog).current_embed.title == "system.music.controls.mode_changed"
