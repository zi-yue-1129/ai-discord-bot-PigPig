"""Fun tools for LLM integration: rolling dice and spinning a decision wheel.

Both post their result in the channel themselves, so the outcome people see is the real random
one rather than something the model wrote.
"""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

import discord
from langchain_core.tools.structured import StructuredTool

from addons.logging import get_logger

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_logger = get_logger(server_id="Bot", source="llm.tools.fun_tools")

MAX_NOTATION = 60
MAX_REASON = 100


class FunTools:
    """Dice and the decision wheel."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        self.runtime = runtime

    def get_tools(self) -> list:
        runtime = self.runtime
        message = getattr(runtime, "message", None)
        guild = getattr(message, "guild", None)
        bot = getattr(runtime, "bot", None)
        if guild is None or bot is None or not hasattr(bot, "get_cog"):
            return []
        language = bot.get_cog("LanguageManager")

        def translate(*keys: str, fallback: str, **kwargs: Any) -> str:
            if language is not None:
                return language.translate(str(guild.id), *keys, **kwargs)
            return fallback.format(**kwargs)

        async def roll_dice(notation: str, reason: Optional[str] = None) -> str:
            """Rolls dice and posts the result in the channel, like /roll.

            Call this whenever someone asks to roll dice (e.g. "roll a d20", "擲兩顆骰子"); never
            make up a dice result yourself.

            Args:
                notation: Dice notation such as d20, 2d6+3 or 4d6-1 ("two dice" = 2d6).
                reason: Optional short note on what the roll is for.

            Returns:
                The roll that was posted, with each die and the total.
            """
            from cogs.story import dice

            try:
                result = dice.roll(str(notation or "")[:MAX_NOTATION])
            except dice.DiceError as error:
                if error.key == "dice_too_many":
                    return f"Too many dice: at most {dice.MAX_DICE} dice with up to {dice.MAX_SIDES} sides each."
                return "That is not dice notation; use something like d20, 2d6+3 or 4d6-1."
            text = translate(
                "story", "addons", "roll_result", fallback="🎲 {user} rolled {result}",
                user=message.author.mention, result=result.describe(),
            )
            reason = " ".join(str(reason or "").split())[:MAX_REASON]
            if reason:
                text += "\n" + translate("story", "addons", "roll_reason", fallback="({reason})", reason=reason)
            try:
                await message.channel.send(text, allowed_mentions=discord.AllowedMentions.none())
            except discord.HTTPException:
                _logger.warning("roll_dice: could not post the roll", exc_info=True)
                return "The roll could not be posted in this channel."
            return f"Posted the roll: {result.describe()}. Do not repeat or change the numbers."

        async def spin_wheel(options: List[str]) -> str:
            """Spins a decision wheel in the channel and lands on one option at random, like /wheel spin.

            Call this when someone asks you to pick or decide randomly between options
            ("help us choose: hot pot, ramen or curry"); never pick yourself.

            Args:
                options: 2 to 20 options, each up to 80 characters.

            Returns:
                The option the wheel landed on.
            """
            wheel = bot.get_cog("WheelCog")
            if wheel is None:
                return "The wheel is not available right now."
            try:
                picked, problem = await wheel.spin_in_channel(message.channel, guild.id, message.author, list(options or []))
            except discord.HTTPException:
                _logger.warning("spin_wheel: could not post the wheel", exc_info=True)
                return "The wheel could not be posted in this channel."
            if problem == "too_few":
                return "The wheel needs at least 2 different options."
            if problem == "busy":
                return "A wheel is already spinning in this channel; try again when it stops."
            from llm.tools.community_tools import user_text

            return f"The wheel landed on {user_text(picked)} (already shown in the channel)."

        fun = {"target_agent_mode": "info", "tool_group": "fun"}
        tools = [StructuredTool.from_function(coroutine=roll_dice, metadata=fun)]
        if bot.get_cog("WheelCog") is not None:
            tools.append(StructuredTool.from_function(coroutine=spin_wheel, metadata=fun))
        return tools
