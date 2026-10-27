"""WebSocket log streamer for real-time dashboard log viewing."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from addons.logging import get_logger
from dashboard.auth.jwt_handler import verify_access_token

log = get_logger(server_id="Bot", source=__name__)
router = APIRouter()


class LogStreamer:
    """Manages WebSocket clients and broadcasts log records."""

    BUFFER_SIZE = 200

    def __init__(self) -> None:
        # Use list instead of set — tuples containing dicts are not hashable
        self._clients: list[tuple[WebSocket, dict[str, Any]]] = []
        self._buffer: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, filters: dict[str, Any] | None = None) -> None:
        """Accept a new WebSocket client and replay recent logs."""
        await websocket.accept()
        entry = (websocket, filters or {})
        async with self._lock:
            self._clients.append(entry)
        for record in self._buffer:
            if self._matches(record, filters or {}):
                try:
                    await websocket.send_text(json.dumps(record, default=repr))
                except Exception:
                    break

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket client."""
        async with self._lock:
            self._clients = [(ws, f) for ws, f in self._clients if ws is not websocket]

    async def broadcast(self, record: dict[str, Any]) -> None:
        """Broadcast a log record to all matching connected clients."""
        self._buffer.append(record)
        if len(self._buffer) > self.BUFFER_SIZE:
            self._buffer = self._buffer[-self.BUFFER_SIZE:]
        dead = []
        # Values such as functions (OpenAI request options carry a post_parser) are sent as text.
        msg = json.dumps(record, default=repr)
        for ws, filters in list(self._clients):
            if not self._matches(record, filters):
                continue
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    @staticmethod
    def _matches(record: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if a log record matches client filters."""
        if filters.get("guild_id") and record.get("server_id") != filters["guild_id"]:
            return False
        if filters.get("level") and record.get("level", "").upper() != filters["level"].upper():
            return False
        return True


log_streamer = LogStreamer()

# How often an open guild log stream re-checks that its viewer may still read it.
GUILD_LOG_RECHECK_SECONDS = 60


def may_read_guild_logs(app: Any, payload: dict[str, Any], guild_id: str) -> bool:
    """Whether a token's holder may stream a guild's logs: the bot owner, or a member who is an
    administrator of that guild right now.

    Guild logs carry the text of every message, private channels included, so being a member is not
    enough. The token's admin list is up to an hour old, so the bot's current view of the member decides.
    """
    if payload.get("role") == "owner":
        return True
    if guild_id not in payload.get("admin_guild_ids", []):
        return False
    bot = getattr(getattr(app, "state", None), "bot", None)
    try:
        guild = bot.get_guild(int(guild_id))
        member = guild.get_member(int(payload.get("sub", 0)))
    except (AttributeError, TypeError, ValueError):
        return False
    return member is not None and bool(member.guild_permissions.administrator)


@router.websocket("/ws/admin/logs")
async def ws_admin_logs(
    websocket: WebSocket,
    guild_id: str | None = Query(default=None),
    level: str | None = Query(default=None),
    token: str | None = Query(default=None),
) -> None:
    """WebSocket endpoint for streaming all logs (Bot Owner only)."""
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    payload = verify_access_token(token)
    if not payload or payload.get("role") != "owner":
        await websocket.close(code=4003, reason="Unauthorized")
        return
    filters = {"guild_id": guild_id, "level": level}
    await log_streamer.connect(websocket, filters)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                update = json.loads(data)
                if "guild_id" in update:
                    filters["guild_id"] = update["guild_id"]
                if "level" in update:
                    filters["level"] = update["level"]
            except (json.JSONDecodeError, TypeError):
                pass
    except WebSocketDisconnect:
        await log_streamer.disconnect(websocket)
    except Exception:
        await log_streamer.disconnect(websocket)


@router.websocket("/ws/guild/{guild_id}/logs")
async def ws_guild_logs(
    websocket: WebSocket,
    guild_id: str,
    level: str | None = Query(default=None),
    token: str | None = Query(default=None),
) -> None:
    """WebSocket endpoint for guild-specific log streaming (the bot owner and the guild's administrators)."""
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=4003, reason="Unauthorized")
        return
    if not may_read_guild_logs(websocket.app, payload, guild_id):
        await websocket.close(code=4003, reason="No access to this guild")
        return
    filters = {"guild_id": guild_id, "level": level}

    def still_allowed() -> bool:
        """Whether the token is still valid and its holder may still read this guild's logs."""
        current = verify_access_token(token)
        return bool(current) and may_read_guild_logs(websocket.app, current, guild_id)

    async def stream() -> bool:
        """Replays and streams records; returns True when it stopped because access ended."""
        await log_streamer.connect(websocket, filters)
        while True:
            data = await websocket.receive_text()
            if not still_allowed():
                return True
            try:
                update = json.loads(data)
                if "level" in update:
                    filters["level"] = update["level"]
            except (json.JSONDecodeError, TypeError):
                pass

    async def watch() -> None:
        """Returns once access has ended. It runs from the start, so a replay that stalls on a client
        that stopped reading cannot postpone a revocation."""
        while True:
            await asyncio.sleep(GUILD_LOG_RECHECK_SECONDS)
            if not still_allowed():
                return

    streaming = asyncio.create_task(stream())
    watching = asyncio.create_task(watch())
    revoked = False
    try:
        done, _ = await asyncio.wait({streaming, watching}, return_when=asyncio.FIRST_COMPLETED)
        if watching in done:
            revoked = True
        elif not streaming.cancelled() and streaming.exception() is None:
            revoked = streaming.result()
        elif not isinstance(streaming.exception(), WebSocketDisconnect):
            log.error("guild log stream ended with an error", exc_info=streaming.exception())
    finally:
        # Also when this handler is cancelled: stop the replay, and never stay subscribed.
        for task in (streaming, watching):
            task.cancel()
        await asyncio.gather(streaming, watching, return_exceptions=True)
        await log_streamer.disconnect(websocket)
    if revoked:
        try:
            await asyncio.wait_for(websocket.close(code=4003, reason="No access to this guild"), timeout=5)
        except Exception:
            # The client already left or stopped reading; it is unsubscribed, so nothing more is sent.
            log.error("could not close a revoked guild log stream", exc_info=True)
