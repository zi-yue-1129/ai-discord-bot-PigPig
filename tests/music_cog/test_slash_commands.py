"""Tests for the /volume, /queue_remove and /queue_clear slash commands."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from music_cog.helpers import (
    GUILD_ID,
    FakeChannel,
    make_interaction,
    make_member,
    make_song,
)

from cogs.music import YTMusic


def _embed_title(interaction: SimpleNamespace) -> str:
    return interaction.response.sent[0]["embed"].title


@pytest.mark.asyncio
async def test_volume_command_sets_the_volume_and_confirms(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, requester: SimpleNamespace,
) -> None:
    interaction = make_interaction(guild, text_channel, requester)

    await cog.volume.callback(cog, interaction, 35)

    assert cog.state_manager.get_state(GUILD_ID).volume == pytest.approx(0.35)
    assert "volume.responses.success" in _embed_title(interaction)
    assert interaction.response.sent[0].get("ephemeral") is None


@pytest.mark.asyncio
async def test_volume_command_explains_why_an_outsider_was_refused(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel,
) -> None:
    interaction = make_interaction(guild, text_channel, make_member(5, voice_channel=object()))

    await cog.volume.callback(cog, interaction, 35)

    assert "not_in_channel" in _embed_title(interaction)
    assert interaction.response.sent[0]["ephemeral"] is True
    assert cog.state_manager.get_state(GUILD_ID).volume == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_queue_remove_command_removes_the_song(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, requester: SimpleNamespace,
    tmp_path: Path,
) -> None:
    for index in range(3):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))
    interaction = make_interaction(guild, text_channel, requester)

    await cog.queue_remove.callback(cog, interaction, 1)

    assert cog.service.queue_titles(GUILD_ID) == ["song 1", "song 2"]
    assert "queue_tools.responses.removed" in _embed_title(interaction)


@pytest.mark.asyncio
async def test_queue_remove_command_reports_an_invalid_position(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, requester: SimpleNamespace,
) -> None:
    interaction = make_interaction(guild, text_channel, requester)

    await cog.queue_remove.callback(cog, interaction, 7)

    assert "invalid_position" in _embed_title(interaction)
    assert interaction.response.sent[0]["ephemeral"] is True


@pytest.mark.asyncio
async def test_queue_clear_command_empties_the_queue(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, requester: SimpleNamespace,
) -> None:
    for index in range(3):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))
    interaction = make_interaction(guild, text_channel, requester)

    await cog.queue_clear.callback(cog, interaction)

    assert cog.service.queue_titles(GUILD_ID) == []
    assert "queue_tools.responses.cleared" in _embed_title(interaction)
