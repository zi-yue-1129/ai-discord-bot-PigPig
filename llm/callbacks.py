from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union
from uuid import UUID
import asyncio
import time

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

from llm.utils.send_message import safe_edit_message


class ToolFeedbackCallbackHandler(AsyncCallbackHandler):
    """Callback handler for providing feedback during tool execution."""

    def __init__(
        self,
        message_edit: Any,
        language_manager: Any,
        guild_id: str
    ):
        self.message_edit = message_edit
        self.language_manager = language_manager
        self.guild_id = guild_id

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool starts running."""
        try:
            tool_name = serialized.get("name", "Unknown Tool")
            
            # Try to get specific message for this tool
            msg = self.language_manager.translate(
                self.guild_id,
                "system", "chat_bot", "responses", "tools", tool_name
            )
            
            # Check if translation was found
            if "Translation not found" in msg or "TRANSLATION_ERROR" in msg:
                # Fallback to default tool message
                status_msg = self.language_manager.translate(
                    self.guild_id,
                    "system", "chat_bot", "responses", "tools", "default",
                    tool_name=tool_name
                )
            else:
                status_msg = msg
            
            # Use asyncio.shield to protect from cancellation and ensure proper loop context
            try:
                await asyncio.shield(safe_edit_message(self.message_edit, status_msg))
            except RuntimeError as e:
                # Suppress Event Loop mismatch errors - these are non-critical
                # The message update is a nice-to-have, not essential for tool execution
                if "loop" not in str(e).lower():
                    raise
        except Exception:
            # Silently ignore callback errors to prevent disrupting tool execution
            pass


class _LogSink(Protocol):
    """What the tool log handler needs from a logger."""

    def info(self, message: str) -> None:
        """Writes an informational line."""

    def error(self, message: str) -> None:
        """Writes an error line."""


class ToolLogCallbackHandler(AsyncCallbackHandler):
    """Writes one log line when a tool starts and one when it ends or fails.

    Unlike :class:`ToolFeedbackCallbackHandler` it never touches Discord and does not need a
    language manager, so it can always be attached and the logs always show which tools ran, how
    long they took and which ones failed.
    """

    def __init__(self, logger: _LogSink, clock: Callable[[], float] = time.monotonic) -> None:
        """Creates the handler.

        Args:
            logger: Where the lines go.
            clock: Source of the current time in seconds; replaced in tests.
        """
        self._logger = logger
        self._clock = clock
        self._running: Dict[UUID, Tuple[str, float]] = {}

    def _finish(self, run_id: UUID) -> Tuple[str, str]:
        """Forgets a running tool and returns (name, how long it ran as text)."""
        name, started = self._running.pop(run_id, ("unknown_tool", None))
        elapsed = f"{self._clock() - started:.2f}s" if started is not None else "unknown time"
        return name, elapsed

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Logs that a tool started, with its (shortened) input."""
        name = str(serialized.get("name", "unknown_tool"))
        self._running[run_id] = (name, self._clock())
        shortened = input_str if len(input_str) <= 200 else input_str[:199] + "…"
        self._logger.info(f"Tool started: {name} input={shortened}")

    async def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Logs that a tool finished, how long it took and how long its answer was."""
        name, elapsed = self._finish(run_id)
        chars = len(str(getattr(output, "content", output)))
        self._logger.info(f"Tool finished: {name} in {elapsed}, {chars} chars")

    async def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        """Logs that a tool raised an error."""
        name, elapsed = self._finish(run_id)
        self._logger.error(f"Tool failed: {name} after {elapsed}: {type(error).__name__}: {error}")
