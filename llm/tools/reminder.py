# MIT License
#
# Copyright (c) 2024 starpig1129
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Reminder tools for LLM integration.

This module provides LangChain-compatible tools for setting reminders
using the ReminderCog.
"""

from datetime import datetime

from addons.logging import get_logger
from typing import Dict, Optional, Set, Tuple, TYPE_CHECKING

from langchain_core.tools import tool

from cogs.remind import ReminderCog
from function import func
from llm.memory.privacy import hidden_in_guild_async

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest


# Module-level logger
_logger = get_logger(server_id="Bot", source="llm.tools.reminder")


class ReminderTools:
    """Container class for reminder management tools.
    
    This class holds the runtime context and provides factory methods
    to create tool instances bound to that context.
    
    Attributes:
        runtime: The orchestrator request containing bot, message, and logger.
    """

    def __init__(self, runtime: "OrchestratorRequest"):
        """Initializes ReminderTools with runtime context.
        
        Args:
            runtime: The orchestrator request object containing necessary context.
        """
        self.runtime = runtime

    def get_tools(self) -> list:
        """Returns a list of LangChain tools bound to this runtime.
        
        Returns:
            A list containing the set_reminder tool with runtime context.
        """
        runtime = self.runtime

        @tool
        async def set_reminder(
            time_str: str, message: str, user_id: Optional[int] = None, repeat: str = "none"
        ) -> str:
            """Sets a reminder for a user at a specified time.

            This tool schedules a reminder that will be sent to the specified user
            (or the message author if not specified) at the given time.

            Args:
                time_str: Time specification string. MUST be one of the following formats:
                    - Relative: "X minutes/hours/days" (e.g. "10 minutes", "2 hours", "1 day")
                    - Absolute: "YYYY-MM-DD HH:MM:SS" (e.g. "2024-12-31 15:30:00")
                    - Natural: "tomorrow at 3pm", "next monday at 9am"
                    Do not use abstract times like "later" or "someday" or the system will fail to parse them.
                message: The reminder message content to be sent.
                user_id: Optional Discord user ID to remind. If not provided,
                    the reminder will be set for the message author. A reminder for
                    someone else must be for a member of this server and cannot repeat.
                repeat: "none" for a one-time reminder, "daily" to repeat every day,
                    or "weekly" to repeat every week at the same time. The first
                    reminder is at time_str.

            Returns:
                A success message with reminder details if scheduled successfully,
                or an error message describing what went wrong.
            """
            logger = getattr(runtime, "logger", _logger)
            
            # Retrieve bot instance from runtime
            bot = getattr(runtime, "bot", None)
            if not bot:
                logger.error("Bot instance not available in runtime.")
                return "Error: Bot instance not available."

            message_obj = getattr(runtime, "message", None)

            # Retrieve ReminderCog
            cog: Optional[ReminderCog] = bot.get_cog("ReminderCog")
            if not cog:
                msg = "Error: ReminderCog is not loaded."
                logger.error(msg)
                return msg

            # Determine target user
            try:
                if user_id is None:
                    # If user_id is not specified, use the requester
                    if message_obj and getattr(message_obj, "author", None):
                        target_user_id = message_obj.author.id
                    else:
                        target_user_id = None
                else:
                    target_user_id = user_id

                # Fetch user object
                try:
                    target_user = (
                        await bot.fetch_user(target_user_id)
                        if target_user_id is not None
                        else None
                    )
                except Exception as fetch_error:
                    # fetch_user may fail; log and use fallback
                    logger.warning(
                        "Failed to fetch user",
                        extra={
                            "user_id": target_user_id,
                            "error": str(fetch_error)
                        }
                    )
                    target_user = None

                # Extract channel and guild information
                channel = getattr(message_obj, "channel", None)
                guild_obj = getattr(message_obj, "guild", None)
                guild_id = str(guild_obj.id) if guild_obj else "@me"

                logger.info(
                    "Setting reminder",
                    extra={
                        "target_user_id": target_user_id,
                        "guild": guild_id,
                        "time_str": time_str
                    },
                )

                # Call reminder logic
                result = await cog._set_reminder_logic(
                    channel=channel,
                    target_user=target_user,
                    time_str=time_str,
                    message=message,
                    guild_id=guild_id,
                    interaction=None,
                    creator=getattr(message_obj, "author", None),
                    repeat=repeat,
                )
                
                logger.info("Reminder scheduled", extra={"result": result})
                return result

            except Exception as e:  # pragma: no cover - orchestrator logic
                await func.report_error(
                    e, f"set_reminder failed for user {user_id}"
                )
                return f"Error: Failed to set reminder: {e}"

        def _reminder_cog_and_user() -> Tuple[Optional[ReminderCog], Optional[int], Optional[str]]:
            """Returns the reminder cog and the asking user's ID, or an error text."""
            bot = getattr(runtime, "bot", None)
            cog: Optional[ReminderCog] = bot.get_cog("ReminderCog") if bot else None
            if cog is None:
                return None, None, "Error: ReminderCog is not loaded."
            author = getattr(getattr(runtime, "message", None), "author", None)
            if author is None:
                return None, None, "Error: the requesting user is unknown."
            return cog, author.id, None

        @tool
        async def list_reminders() -> str:
            """Lists the pending reminders the requesting user has set, and those others set for them.

            Call this when the user asks what reminders they have, or before cancelling
            one to find its ID. Only reminders the requesting user set or receives are listed.

            Returns:
                One line per reminder with its ID, due time, target and text, or a note
                that there are none.
            """
            cog, user_id, error = _reminder_cog_and_user()
            if error:
                return error
            pending = cog.store.list_for_creator(user_id)
            from_others = cog.store.list_from_others(user_id)
            if not pending and not from_others:
                return "You have no pending reminders."
            # Members who hid with /leaderboard optout are not named to anyone else; when a server's
            # opt-out list cannot be read nobody is named.
            # The answer is read in the server it is given in, so that server's list counts too.
            answering_guild = getattr(getattr(runtime, "message", None), "guild", None)
            hidden_here: Optional[Set[int]] = set()
            if answering_guild is not None:
                hidden_here = await hidden_in_guild_async(getattr(runtime, "bot", None), answering_guild.id)
            hidden_by_guild: Dict[str, Optional[Set[int]]] = {}
            for reminder in pending + from_others:
                if reminder.guild_id not in hidden_by_guild:
                    try:
                        hidden_by_guild[reminder.guild_id] = await hidden_in_guild_async(
                            getattr(runtime, "bot", None), int(reminder.guild_id)
                        )
                    except ValueError:
                        # Direct-message reminders ("@me") belong to no server, so there is no list to read.
                        hidden_by_guild[reminder.guild_id] = None
            lines = []
            for title, reminders in (
                ("Pending reminders you set (ID | due | target | text):", pending),
                ("Pending reminders others set for you; you may cancel them (ID | due | set by | text):", from_others),
            ):
                if not reminders:
                    continue
                lines.append(title)
                for reminder in reminders:
                    due = datetime.fromtimestamp(reminder.due_at).strftime("%Y-%m-%d %H:%M")
                    person_id = reminder.target_id if reminder.creator_id == user_id else reminder.creator_id
                    hidden = hidden_by_guild[reminder.guild_id]
                    concealed = hidden is None or hidden_here is None or person_id in hidden or person_id in hidden_here
                    person = "a member" if person_id != user_id and concealed else f"<@{person_id}>"
                    lines.append(f"#{reminder.id} | {due} (unix {int(reminder.due_at)}) | {person} | {reminder.message}")
            return "\n".join(lines)

        @tool
        async def cancel_reminder(reminder_id: int) -> str:
            """Cancels a pending reminder the requesting user set, or one someone else set for them.

            Use list_reminders first if the ID is not known. A user can only cancel
            reminders they set themselves or that are for them.

            Args:
                reminder_id: The reminder's ID, as shown by list_reminders.

            Returns:
                A confirmation naming the cancelled reminder, or a not-found message.
            """
            cog, user_id, error = _reminder_cog_and_user()
            if error:
                return error
            mine = {
                reminder.id: reminder
                for reminder in cog.store.list_for_creator(user_id) + cog.store.list_from_others(user_id)
            }
            if reminder_id not in mine or not cog.store.cancel(reminder_id, user_id):
                return f"Reminder #{reminder_id} was not found among your pending reminders."
            return f"Cancelled reminder #{reminder_id}: {mine[reminder_id].message}"

        return [set_reminder, list_reminders, cancel_reminder]
