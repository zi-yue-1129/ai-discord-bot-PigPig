"""Guild log streams carry every message's text, so only the owner and the guild's administrators get them."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from dashboard.websocket import log_streamer as streamer_module

GUILD_ID = "111"
MEMBER_ID = "222"


def _bot(administrator: Optional[bool]) -> Any:
    """A bot whose guild 111 has member 222 with or without Administrator (None: not a member)."""
    member = None
    if administrator is not None:
        member = SimpleNamespace(guild_permissions=SimpleNamespace(administrator=administrator))
    guild = SimpleNamespace(get_member=lambda user_id: member if user_id == int(MEMBER_ID) else None)
    return SimpleNamespace(get_guild=lambda guild_id: guild if guild_id == int(GUILD_ID) else None)


def _payload(role: str = "admin", admin_guilds: tuple = (GUILD_ID,)) -> Dict[str, Any]:
    return {"sub": MEMBER_ID, "role": role, "guild_ids": [GUILD_ID], "admin_guild_ids": list(admin_guilds)}


def _app(bot: Any) -> FastAPI:
    app = FastAPI()
    app.state.bot = bot
    app.include_router(streamer_module.router)
    return app


@pytest.fixture(autouse=True)
def _fresh_streamer(monkeypatch: pytest.MonkeyPatch) -> streamer_module.LogStreamer:
    streamer = streamer_module.LogStreamer()
    monkeypatch.setattr(streamer_module, "log_streamer", streamer)
    return streamer


def _connect(app: FastAPI, monkeypatch: pytest.MonkeyPatch, payload: Optional[Dict[str, Any]]) -> Optional[int]:
    """Opens the guild log stream and returns the close code, or None when it stays open."""
    monkeypatch.setattr(streamer_module, "verify_access_token", lambda token: payload)
    client = TestClient(app)
    try:
        with client.websocket_connect(f"/ws/guild/{GUILD_ID}/logs?token=t") as socket:
            socket.send_text("{}")
            socket.close()
    except WebSocketDisconnect as closed:
        return closed.code
    return None


def test_a_plain_member_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(role="user", admin_guilds=())
    assert _connect(_app(_bot(administrator=False)), monkeypatch, payload) == 4003


def test_an_admin_claim_without_current_administrator_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _connect(_app(_bot(administrator=False)), monkeypatch, _payload()) == 4003


def test_a_member_who_left_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _connect(_app(_bot(administrator=None)), monkeypatch, _payload()) == 4003


def test_a_current_administrator_may_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _connect(_app(_bot(administrator=True)), monkeypatch, _payload()) is None


def test_the_owner_may_stream_any_guild(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(role="owner", admin_guilds=())
    assert _connect(_app(_bot(administrator=None)), monkeypatch, payload) is None


def test_an_expired_token_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _connect(_app(_bot(administrator=True)), monkeypatch, None) == 4003


def test_a_refused_member_gets_no_buffered_record(
    monkeypatch: pytest.MonkeyPatch, _fresh_streamer: streamer_module.LogStreamer
) -> None:
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_fresh_streamer.broadcast({"server_id": GUILD_ID, "message": "private text"}))
    finally:
        loop.close()
    monkeypatch.setattr(streamer_module, "verify_access_token", lambda token: _payload(role="user", admin_guilds=()))
    client = TestClient(_app(_bot(administrator=False)))
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/guild/{GUILD_ID}/logs?token=t") as socket:
            socket.receive_text()


def test_losing_administrator_closes_an_open_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    permissions = SimpleNamespace(administrator=True)
    member = SimpleNamespace(guild_permissions=permissions)
    guild = SimpleNamespace(get_member=lambda user_id: member)
    app = _app(SimpleNamespace(get_guild=lambda guild_id: guild))
    monkeypatch.setattr(streamer_module, "verify_access_token", lambda token: _payload())
    client = TestClient(app)
    with client.websocket_connect(f"/ws/guild/{GUILD_ID}/logs?token=t") as socket:
        permissions.administrator = False
        socket.send_text("{}")
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_text()
    assert closed.value.code == 4003
