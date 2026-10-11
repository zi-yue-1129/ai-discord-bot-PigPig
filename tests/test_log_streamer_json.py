"""The dashboard log stream must survive log records that contain functions."""

from __future__ import annotations

import json
from typing import List

import pytest

from dashboard.websocket.log_streamer import LogStreamer


class _Socket:
    """A WebSocket stand-in that records what is sent to it."""

    def __init__(self) -> None:
        self.sent: List[str] = []

    async def accept(self) -> None:
        return None

    async def send_text(self, text: str) -> None:
        self.sent.append(text)


def _parser(value: str) -> str:
    return value


def _record() -> dict:
    return {"level": "DEBUG", "server_id": "Bot", "message": "Request options", "extra": {"post_parser": _parser}}


@pytest.mark.asyncio
async def test_a_record_with_a_function_is_broadcast_as_text() -> None:
    streamer = LogStreamer()
    socket = _Socket()
    await streamer.connect(socket)

    await streamer.broadcast(_record())

    assert "_parser" in json.loads(socket.sent[0])["extra"]["post_parser"]


@pytest.mark.asyncio
async def test_a_new_client_still_gets_the_buffered_record_with_a_function() -> None:
    streamer = LogStreamer()
    await streamer.broadcast(_record())
    late = _Socket()

    await streamer.connect(late)

    assert len(late.sent) == 1
    assert json.loads(late.sent[0])["message"] == "Request options"
