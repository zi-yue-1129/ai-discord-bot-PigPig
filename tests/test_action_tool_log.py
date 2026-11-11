"""Action-tool logging."""
import asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from llm.callbacks import ToolLogCallbackHandler


def test_tool_log_records_started_names():
    handler = ToolLogCallbackHandler(MagicMock())
    asyncio.run(handler.on_tool_start({"name": "change_own_nickname"}, "{}", run_id=uuid4()))
    assert handler.started == ["change_own_nickname"]
