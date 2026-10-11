"""User-visible progress messages for the chat pipeline."""

from __future__ import annotations

from typing import Any, Optional

from addons.logging import get_logger
from llm.utils.send_message import safe_edit_message

logger = get_logger(server_id="Bot", source=__name__)

_DEFAULT_SWITCH_TEXT = "⏳ The model did not respond, switching to a backup model..."


async def announce_model_switch(
    message_edit: Any, lang_manager: Optional[Any], guild_id: str, has_next_model: bool
) -> None:
    """Tells the user the pipeline is moving on to the next model after a failure.

    Without this the status message keeps saying "analyzing" or "thinking" while the next
    model is tried, which looks like the bot is stuck.

    Args:
        message_edit: The status message shown to the user.
        lang_manager: The language manager, or None for the English default.
        guild_id: The guild whose language is used.
        has_next_model: Whether another model will be tried; nothing is shown otherwise.
    """
    if not has_next_model:
        return
    text = (
        lang_manager.translate(guild_id, "system", "chat_bot", "responses", "switching_model")
        if lang_manager
        else _DEFAULT_SWITCH_TEXT
    )
    try:
        await safe_edit_message(message_edit, text)
    except Exception:
        # The status text is a courtesy; the reply must still be produced if the edit fails.
        logger.error("Could not show the model switch notice", exc_info=True)
