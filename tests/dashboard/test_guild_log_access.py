"""Guild log streams carry every message's text, so only the owner and the guild's administrators get them."""

from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace
from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from starlette.websockets import WebSocketDisconnect

from dashboard.auth import jwt_handler
from dashboard.auth.jwt_handler import create_access_token
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


def _signed_token(expires_at: Optional[int] = None) -> str:
    """A token signed with the dashboard's key, so the real verification (signature and expiry) runs."""
    if expires_at is None:
        return create_access_token(MEMBER_ID, "admin", [GUILD_ID], [GUILD_ID])
    claims = {**_payload(), "iat": time.time(), "exp": expires_at}
    return jwt.encode(claims, jwt_handler._SECRET_KEY, algorithm=jwt_handler.ALGORITHM)


class _StalledSocket:
    """A client that stopped reading: every send waits forever, and it never sends anything."""

    def __init__(self, app: FastAPI, stall_sends: bool = True) -> None:
        self.app = app
        self.stall_sends = stall_sends
        self.sent: list = []
        self.closed: list = []
        self._never = asyncio.Event()

    async def accept(self) -> None:
        """Accepts the connection."""

    async def send_text(self, text: str) -> None:
        """Records the record; a stalled client never finishes receiving it."""
        self.sent.append(text)
        if self.stall_sends:
            await self._never.wait()

    async def receive_text(self) -> str:
        """An idle client: nothing arrives."""
        await self._never.wait()
        return ""

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Records the close code."""
        self.closed.append(code)


async def _until(condition: Any) -> None:
    """Yields to the event loop until ``condition()`` holds, failing instead of hanging."""
    for _ in range(400):
        if condition():
            break
        await asyncio.sleep(0.005)
    else:
        raise AssertionError("the awaited state was never reached")


@pytest.mark.asyncio
async def test_losing_administrator_while_the_replay_is_stalled_ends_the_stream(
    monkeypatch: pytest.MonkeyPatch, _fresh_streamer: streamer_module.LogStreamer
) -> None:
    """A client that does not read must not keep the replay, and the stream, alive past a revocation."""
    permissions = SimpleNamespace(administrator=True)
    guild = SimpleNamespace(get_member=lambda user_id: SimpleNamespace(guild_permissions=permissions))
    socket = _StalledSocket(_app(SimpleNamespace(get_guild=lambda guild_id: guild)))
    _fresh_streamer._buffer.append({"server_id": GUILD_ID, "level": "INFO", "message": "private text"})
    monkeypatch.setattr(streamer_module, "GUILD_LOG_RECHECK_SECONDS", 0.02)

    handler = asyncio.create_task(streamer_module.ws_guild_logs(socket, GUILD_ID, None, _signed_token()))
    await _until(lambda: socket.sent)
    permissions.administrator = False
    await asyncio.wait_for(handler, timeout=2)

    assert socket.closed == [4003]
    assert _fresh_streamer._clients == []


@pytest.mark.asyncio
async def test_an_idle_stream_ends_when_the_token_expires(
    monkeypatch: pytest.MonkeyPatch, _fresh_streamer: streamer_module.LogStreamer
) -> None:
    """No client input arrives, so only the periodic check can notice the expiry."""
    member = SimpleNamespace(guild_permissions=SimpleNamespace(administrator=True))
    guild = SimpleNamespace(get_member=lambda user_id: member)
    socket = _StalledSocket(_app(SimpleNamespace(get_guild=lambda guild_id: guild)), stall_sends=False)
    monkeypatch.setattr(streamer_module, "GUILD_LOG_RECHECK_SECONDS", 0.02)
    # A real signed token that is valid now and expires within two seconds (exp has second resolution).
    token = _signed_token(expires_at=int(time.time()) + 1)

    await asyncio.wait_for(streamer_module.ws_guild_logs(socket, GUILD_ID, None, token), timeout=5)

    assert socket.closed == [4003]
    assert _fresh_streamer._clients == []


@pytest.mark.asyncio
async def test_a_cancelled_stream_is_removed_from_the_subscribers(
    monkeypatch: pytest.MonkeyPatch, _fresh_streamer: streamer_module.LogStreamer
) -> None:
    """A cancelled handler must not stay subscribed to later records."""
    member = SimpleNamespace(guild_permissions=SimpleNamespace(administrator=True))
    guild = SimpleNamespace(get_member=lambda user_id: member)
    socket = _StalledSocket(_app(SimpleNamespace(get_guild=lambda guild_id: guild)), stall_sends=False)

    handler = asyncio.create_task(streamer_module.ws_guild_logs(socket, GUILD_ID, None, _signed_token()))
    await _until(lambda: _fresh_streamer._clients)
    handler.cancel()
    with pytest.raises(asyncio.CancelledError):
        await handler

    assert _fresh_streamer._clients == []


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
