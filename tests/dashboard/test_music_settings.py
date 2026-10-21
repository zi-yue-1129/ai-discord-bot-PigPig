"""Tests for the dashboard music settings endpoints (``/api/guild/{id}/music``)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cogs.music_lib.music_store import MusicStore
from dashboard.middleware.permission import get_current_user
from dashboard.routers import guild as guild_module

GUILD_ID = 111111111111111111
EVERYONE_ID = GUILD_ID
DJ_ROLE_ID = 222222222222222222
TEXT_ID = 333333333333333333
OTHER_TEXT_ID = 333333333333333334
VOICE_ID = 444444444444444444
STAGE_ID = 555555555555555555
FOREIGN_ID = 999999999999999999


def _item(item_id: int, name: str, position: int) -> SimpleNamespace:
    return SimpleNamespace(id=item_id, name=name, position=position)


def _make_guild() -> SimpleNamespace:
    everyone = _item(EVERYONE_ID, "@everyone", 0)
    return SimpleNamespace(
        id=GUILD_ID,
        name="Test Guild",
        default_role=everyone,
        roles=[everyone, _item(DJ_ROLE_ID, "DJ", 1), _item(DJ_ROLE_ID + 1, "Mods", 2)],
        text_channels=[_item(OTHER_TEXT_ID, "chat", 1), _item(TEXT_ID, "song-requests", 0)],
        voice_channels=[_item(VOICE_ID, "Music", 0)],
        stage_channels=[_item(STAGE_ID, "Stage", 1)],
    )


def _make_cog(tmp_path) -> SimpleNamespace:
    store = MusicStore(tmp_path / "music.db")

    async def _enable(guild: Any, channel: Any) -> bool:
        store.update_settings(guild.id, request_channel_id=channel.id, request_message_id=1)
        return True

    async def _disable(guild: Any) -> None:
        store.update_settings(guild.id, request_channel_id=None, request_message_id=None)

    return SimpleNamespace(
        store=store,
        requests=SimpleNamespace(enable=AsyncMock(side_effect=_enable), disable=AsyncMock(side_effect=_disable)),
        stay_in=AsyncMock(return_value=True),
        leave_if_idle=AsyncMock(return_value=None),
    )


@pytest.fixture()
def guild() -> SimpleNamespace:
    return _make_guild()


@pytest.fixture()
def cog(tmp_path) -> SimpleNamespace:
    return _make_cog(tmp_path)


def _client(guild: Any, cog: Any, user: dict | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(guild_module.router)
    bot = MagicMock()
    bot.get_guild.side_effect = lambda gid: guild if guild is not None and gid == guild.id else None
    bot.get_cog.side_effect = lambda name: cog if name == "YTMusic" else None
    app.state.bot = bot
    payload = user or {"sub": "1", "role": "owner", "guild_ids": []}
    app.dependency_overrides[get_current_user] = lambda: payload
    return TestClient(app, raise_server_exceptions=False)


URL = f"/api/guild/{GUILD_ID}/music"


# ---------------------------------------------------------------------- GET


def test_get_returns_settings_and_options(guild, cog):
    response = _client(guild, cog).get(URL)
    assert response.status_code == 200
    data = response.json()
    assert data["settings"]["dj_role_id"] is None
    assert data["settings"]["default_volume"] == 100
    assert data["settings"]["vote_ratio"] == 0.5
    # @everyone skipped, highest role first, IDs as strings
    assert data["roles"] == [{"id": str(DJ_ROLE_ID + 1), "name": "Mods"}, {"id": str(DJ_ROLE_ID), "name": "DJ"}]
    assert data["text_channels"] == [
        {"id": str(TEXT_ID), "name": "song-requests"},
        {"id": str(OTHER_TEXT_ID), "name": "chat"},
    ]
    assert data["voice_channels"] == [{"id": str(VOICE_ID), "name": "Music"}, {"id": str(STAGE_ID), "name": "Stage"}]


def test_get_ids_are_strings(guild, cog):
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE_ID)
    data = _client(guild, cog).get(URL).json()
    assert data["settings"]["dj_role_id"] == str(DJ_ROLE_ID)


def test_get_unknown_guild_is_404(cog):
    response = _client(None, cog).get(URL)
    assert response.status_code == 404


def test_get_without_music_cog_is_503(guild):
    response = _client(guild, None).get(URL)
    assert response.status_code == 503


def test_get_requires_guild_admin(guild, cog):
    user = {"sub": "5", "role": "user", "guild_ids": [str(GUILD_ID)], "admin_guild_ids": []}
    response = _client(guild, cog, user).get(URL)
    assert response.status_code == 403


# ---------------------------------------------------------------------- PUT


def test_put_updates_plain_fields(guild, cog):
    response = _client(guild, cog).put(URL, json={
        "dj_role_id": str(DJ_ROLE_ID),
        "vote_ratio": 0.75,
        "default_volume": 40,
        "stage_announce": True,
    })
    assert response.status_code == 200, response.text
    settings = response.json()["settings"]
    assert settings["dj_role_id"] == str(DJ_ROLE_ID)
    assert settings["vote_ratio"] == 0.75
    assert settings["default_volume"] == 40
    assert settings["stage_announce"] is True
    stored = cog.store.get_settings(GUILD_ID)
    assert stored.dj_role_id == DJ_ROLE_ID and stored.default_volume == 40
    cog.requests.enable.assert_not_awaited()
    cog.stay_in.assert_not_awaited()


def test_put_clears_dj_role(guild, cog):
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE_ID)
    response = _client(guild, cog).put(URL, json={"dj_role_id": None})
    assert response.status_code == 200
    assert cog.store.get_settings(GUILD_ID).dj_role_id is None


@pytest.mark.parametrize("body", [
    {"dj_role_id": str(FOREIGN_ID)},
    {"dj_role_id": str(EVERYONE_ID)},
    {"dj_role_id": str(TEXT_ID)},
    {"dj_role_id": "not-an-id"},
    {"request_channel_id": str(FOREIGN_ID)},
    {"request_channel_id": str(VOICE_ID)},
    {"stay_channel_id": str(TEXT_ID)},
    {"default_volume": 101},
    {"default_volume": -1},
    {"default_volume": 50.5},
    {"default_volume": "50"},
    {"vote_ratio": 0.05},
    {"vote_ratio": 1.5},
    {"stage_announce": "yes"},
    {"request_message_id": "1"},
])
def test_put_rejects_invalid_input(guild, cog, body):
    response = _client(guild, cog).put(URL, json=body)
    assert response.status_code == 400, body
    assert response.json()["detail"]


def test_put_invalid_input_changes_nothing(guild, cog):
    response = _client(guild, cog).put(URL, json={"default_volume": 30, "dj_role_id": str(FOREIGN_ID)})
    assert response.status_code == 400
    assert cog.store.get_settings(GUILD_ID).default_volume == 100


def test_put_request_channel_enable(guild, cog):
    response = _client(guild, cog).put(URL, json={"request_channel_id": str(TEXT_ID)})
    assert response.status_code == 200
    assert response.json()["settings"]["request_channel_id"] == str(TEXT_ID)
    cog.requests.enable.assert_awaited_once()
    assert cog.requests.enable.await_args.args[1].id == TEXT_ID


def test_put_request_channel_enable_failure_is_400(guild, cog):
    cog.requests.enable = AsyncMock(return_value=False)
    response = _client(guild, cog).put(URL, json={"request_channel_id": str(TEXT_ID), "default_volume": 20})
    assert response.status_code == 400
    assert "Manage Messages" in response.json()["detail"]
    settings = cog.store.get_settings(GUILD_ID)
    assert settings.request_channel_id is None
    assert settings.default_volume == 100


def test_put_request_channel_unchanged_does_not_repost(guild, cog):
    cog.store.update_settings(GUILD_ID, request_channel_id=TEXT_ID)
    response = _client(guild, cog).put(URL, json={"request_channel_id": str(TEXT_ID)})
    assert response.status_code == 200
    cog.requests.enable.assert_not_awaited()


def test_put_request_channel_disable(guild, cog):
    cog.store.update_settings(GUILD_ID, request_channel_id=TEXT_ID)
    response = _client(guild, cog).put(URL, json={"request_channel_id": None})
    assert response.status_code == 200
    cog.requests.disable.assert_awaited_once_with(guild)
    assert response.json()["settings"]["request_channel_id"] is None


def test_put_stay_247_on_joins_channel(guild, cog):
    response = _client(guild, cog).put(URL, json={"stay_247": True, "stay_channel_id": str(STAGE_ID)})
    assert response.status_code == 200
    settings = cog.store.get_settings(GUILD_ID)
    assert settings.stay_247 is True and settings.stay_channel_id == STAGE_ID
    cog.stay_in.assert_awaited_once()
    assert cog.stay_in.await_args.args[1].id == STAGE_ID
    assert "warning" not in response.json()


def test_put_stay_247_on_uses_saved_channel(guild, cog):
    cog.store.update_settings(GUILD_ID, stay_channel_id=VOICE_ID)
    response = _client(guild, cog).put(URL, json={"stay_247": True})
    assert response.status_code == 200
    assert cog.stay_in.await_args.args[1].id == VOICE_ID


def test_put_stay_247_on_without_channel_is_400(guild, cog):
    response = _client(guild, cog).put(URL, json={"stay_247": True})
    assert response.status_code == 400
    assert cog.store.get_settings(GUILD_ID).stay_247 is False
    cog.stay_in.assert_not_awaited()


def test_put_stay_247_join_failure_returns_warning(guild, cog):
    cog.stay_in = AsyncMock(return_value=False)
    response = _client(guild, cog).put(URL, json={"stay_247": True, "stay_channel_id": str(VOICE_ID)})
    assert response.status_code == 200
    assert response.json()["warning"]
    assert cog.store.get_settings(GUILD_ID).stay_247 is True


def test_put_stay_247_off_leaves_if_idle(guild, cog):
    cog.store.update_settings(GUILD_ID, stay_247=True, stay_channel_id=VOICE_ID)
    response = _client(guild, cog).put(URL, json={"stay_247": False})
    assert response.status_code == 200
    assert cog.store.get_settings(GUILD_ID).stay_247 is False
    cog.leave_if_idle.assert_awaited_once_with(GUILD_ID)
    cog.stay_in.assert_not_awaited()


def test_put_stay_247_unchanged_does_not_rejoin(guild, cog):
    cog.store.update_settings(GUILD_ID, stay_247=True, stay_channel_id=VOICE_ID)
    response = _client(guild, cog).put(URL, json={"stay_247": True, "stay_channel_id": str(VOICE_ID)})
    assert response.status_code == 200
    cog.stay_in.assert_not_awaited()
    cog.leave_if_idle.assert_not_awaited()


def test_put_without_music_cog_is_503(guild):
    response = _client(guild, None).put(URL, json={"default_volume": 10})
    assert response.status_code == 503
