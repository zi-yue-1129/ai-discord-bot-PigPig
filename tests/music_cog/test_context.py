"""Tests for the playback context and voice-channel authorization helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cogs.music_lib.context import (
    PlaybackContext,
    user_shares_voice_channel,
)


def _interaction(guild: object, channel: object, user: object) -> SimpleNamespace:
    """Builds a minimal stand-in for ``discord.Interaction``."""
    return SimpleNamespace(guild=guild, channel=channel, user=user)


def test_from_interaction_copies_guild_channel_and_user() -> None:
    guild, channel, user = object(), object(), object()

    ctx = PlaybackContext.from_interaction(_interaction(guild, channel, user))

    assert ctx.guild is guild
    assert ctx.channel is channel
    assert ctx.user is user


def test_from_message_uses_the_author_as_requester() -> None:
    guild, channel, author = object(), object(), object()
    message = SimpleNamespace(guild=guild, channel=channel, author=author)

    ctx = PlaybackContext.from_message(message)

    assert (ctx.guild, ctx.channel, ctx.user) == (guild, channel, author)


def test_from_interaction_rejects_dm_interactions() -> None:
    with pytest.raises(ValueError, match="guild"):
        PlaybackContext.from_interaction(_interaction(None, object(), object()))


def test_coerce_returns_an_existing_context_unchanged() -> None:
    ctx = PlaybackContext(guild=object(), channel=object(), user=object())

    assert PlaybackContext.coerce(ctx) is ctx


def test_coerce_converts_an_interaction() -> None:
    guild, channel, user = object(), object(), object()

    ctx = PlaybackContext.coerce(_interaction(guild, channel, user))

    assert isinstance(ctx, PlaybackContext)
    assert ctx.guild is guild


def _member(voice_channel: object | None) -> SimpleNamespace:
    voice = None if voice_channel is None else SimpleNamespace(channel=voice_channel)
    return SimpleNamespace(voice=voice)


def test_user_in_the_same_voice_channel_may_control_playback() -> None:
    channel = object()

    assert user_shares_voice_channel(_member(channel), SimpleNamespace(channel=channel))


def test_user_in_another_voice_channel_may_not_control_playback() -> None:
    voice_client = SimpleNamespace(channel=object())

    assert not user_shares_voice_channel(_member(object()), voice_client)


def test_user_outside_any_voice_channel_may_not_control_playback() -> None:
    assert not user_shares_voice_channel(_member(None), SimpleNamespace(channel=object()))


def test_missing_voice_client_means_there_is_nothing_to_control() -> None:
    assert not user_shares_voice_channel(_member(object()), None)
