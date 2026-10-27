"""Confirm and Cancel buttons that ask one member to approve a step the AI proposed for them.

The AI's tools never change a member's saved state on the model's word alone: they post one of
these, and the step runs only when that member presses Confirm themselves.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Hashable, Optional, Union

import discord

from addons.logging import get_logger

_logger = get_logger(server_id="Bot", source="confirm")

# How long a member has to answer.
ASK_SECONDS = 180


class ConfirmView(discord.ui.View):
    """Runs ``on_confirm`` once, when ``owner_id`` presses Confirm.

    Args:
        owner_id: The only member who may press the buttons.
        text: Translates a key: "ask_confirm", "ask_cancel" (button labels), "ask_not_yours",
            "ask_done", "ask_cancelled", "ask_expired" and "ask_replaced".
        on_confirm: Does the step and returns what the message says afterwards.
        pending: Where the open question is kept under ``key``; a newer question for the same key
            replaces it (see ``ask``), and it is removed once answered.
    """

    def __init__(
        self,
        owner_id: int,
        text: Callable[[str], str],
        on_confirm: Callable[[], Awaitable[str]],
        pending: Optional[Dict[Hashable, "ConfirmView"]] = None,
        key: Hashable = None,
        timeout: float = ASK_SECONDS,
    ) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.text = text
        self.on_confirm = on_confirm
        self.pending = pending
        self.key = key
        self.message: Any = None
        # Set before the first await of a press, so a second press can never run the step twice.
        self.done = False
        for item, label in zip(self.children, ("ask_confirm", "ask_cancel")):
            item.label = text(label)

    def _finish(self) -> bool:
        """Marks the question answered; False when it already was."""
        if self.done:
            return False
        self.done = True
        self.stop()
        if self.pending is not None and self.pending.get(self.key) is self:
            del self.pending[self.key]
        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(self.text("ask_not_yours"), ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="✅", label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self._finish():
            await interaction.response.send_message(self.text("ask_done"), ephemeral=True)
            return
        # Acknowledged first: the step may wait for a lock longer than Discord's 3 seconds.
        await interaction.response.defer()
        content = await self.on_confirm()
        await interaction.edit_original_response(content=content, view=None)

    @discord.ui.button(emoji="✖️", label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self._finish():
            await interaction.response.send_message(self.text("ask_done"), ephemeral=True)
            return
        await interaction.response.edit_message(content=self.text("ask_cancelled"), view=None)

    async def _close(self, key: str) -> None:
        if not self._finish() or self.message is None:
            return
        try:
            await self.message.edit(content=self.text(key), view=None)
        except discord.HTTPException:
            pass

    async def on_timeout(self) -> None:
        await self._close("ask_expired")

    async def replace(self) -> None:
        """Closes this question because a newer one for the same thing was asked."""
        await self._close("ask_replaced")


async def ask(
    channel: Any,
    content: Union[str, Callable[[], str]],
    view: ConfirmView,
    allowed_mentions: Optional[discord.AllowedMentions] = None,
) -> ConfirmView:
    """Posts ``view`` under ``content``, replacing the open question under its key.

    ``content`` may be a function, called only once the replaced question is closed, so the text
    reflects what may be shown at the moment it is posted. Nobody is pinged unless
    ``allowed_mentions`` names them.
    """
    previous = None
    if view.pending is not None:
        previous = view.pending.get(view.key)
        view.pending[view.key] = view
    try:
        if previous is not None:
            await previous.replace()
        text = content() if callable(content) else content
        view.message = await channel.send(
            text, view=view, allowed_mentions=allowed_mentions or discord.AllowedMentions.none()
        )
    except BaseException:
        # Also when the task is cancelled, so the key is never left reserved.
        view._finish()
        raise
    if view.done:
        # A newer question replaced this one while it was being sent: its buttons would never work.
        await close_late(view.message, view.text("ask_replaced"))
    return view


async def close_late(message: Any, content: str) -> None:
    """Turns a question that was answered or replaced before its message existed into ``content``.

    Tried twice; if both edits fail the message is deleted, so dead buttons never stay up.
    """
    for _ in range(2):
        try:
            await message.edit(content=content, view=None)
            return
        except discord.HTTPException:
            continue
    try:
        await message.delete()
    except discord.HTTPException:
        _logger.warning("could not close or delete a replaced question", exc_info=True)
