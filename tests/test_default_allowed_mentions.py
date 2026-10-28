"""No message the bot sends may ping @everyone, @here or a role unless that send allows it itself."""

from __future__ import annotations

from typing import Any, Dict

import discord
import pytest
from discord.ext import commands

from bot import DEFAULT_ALLOWED_MENTIONS, PigPig


class _Stop(Exception):
    """Ends PigPig's setup right after discord.py receives its options."""


def _options(monkeypatch: pytest.MonkeyPatch, **kwargs: Any) -> Dict[str, Any]:
    """The options PigPig hands to discord.py's Bot."""
    seen: Dict[str, Any] = {}

    def capture(self: Any, *args: Any, **options: Any) -> None:
        seen.update(options)
        raise _Stop

    monkeypatch.setattr(commands.Bot, "__init__", capture)
    with pytest.raises(_Stop):
        PigPig(command_prefix="!", **kwargs)
    return seen


def test_the_bot_blocks_everyone_and_role_pings_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    mentions = _options(monkeypatch)["allowed_mentions"]

    assert mentions is DEFAULT_ALLOWED_MENTIONS
    assert mentions.everyone is False
    assert mentions.roles is False
    assert mentions.users is True
    assert mentions.replied_user is True


def test_an_explicit_setting_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    quiet = discord.AllowedMentions.none()

    assert _options(monkeypatch, allowed_mentions=quiet)["allowed_mentions"] is quiet
