# MIT License

# Copyright (c) 2024 starpig1129

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import re
import time
import dateparser

from typing import Any, Dict, Optional
from .language_manager import LanguageManager
from .remind_lib.store import REPEAT_CHOICES, Reminder, ReminderStore, next_occurrence
from function import func
from addons.confirm import ConfirmView, ask
from addons.rate_limiter import format_wait
from addons.settings import base_config
from addons.logging import get_logger
from llm.reminder_writer import LATE_THRESHOLD_SECONDS, ReminderRequest, compose_reminder

REMINDER_DB_PATH = "data/reminders.db"
# Longest part of a reminder's text quoted in the question to the member it is for.
ASK_PREVIEW_CHARS = 500


def _shorten(text: str) -> str:
    return text if len(text) <= ASK_PREVIEW_CHARS else text[:ASK_PREVIEW_CHARS].rstrip() + "…"


def _limit(config: Any, key: str, default: int) -> int:
    """A whole, non-negative limit from the ``reminders:`` block of base.yaml; ``default`` when unusable."""
    value = config.get(key, default) if isinstance(config, dict) else default
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return default
    return value


class ReminderCog(commands.Cog):
    """Sets reminders and, when each falls due, has the model write it from the recent chat."""

    MAX_PENDING_PER_USER = 20
    # Pending reminders other people may set for one member; the owner can change it in base.yaml.
    MAX_PENDING_FROM_OTHERS = 3
    MAX_HORIZON_SECONDS = 365 * 24 * 3600
    MAX_DELIVERY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 60
    MAX_SLEEP_SECONDS = 30

    # Read by llm.self_knowledge so the bot can explain reminders when asked.
    GUIDE_NOTES = (
        "When a reminder is due the bot writes it in its own words from the recent chat and mentions only the "
        "person it is for. Reminders survive restarts. In chat the bot can also set, list and cancel a "
        f"member's reminders when asked. Each member can have at most {MAX_PENDING_PER_USER} pending reminders. "
        "A reminder for someone else must be for a member of the server and is only set once that member "
        "presses Accept; they can see it with /reminders and cancel it."
    )

    def __init__(self, bot):
        self.bot = bot
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="remind")
        self.store = ReminderStore(REMINDER_DB_PATH)
        limits = getattr(base_config, "reminders", None) or {}
        self.max_pending_per_user = _limit(limits, "max_pending_per_user", self.MAX_PENDING_PER_USER)
        self.max_pending_from_others = _limit(limits, "max_pending_from_others", self.MAX_PENDING_FROM_OTHERS)
        self._now = time.time
        self._wake: Optional[asyncio.Event] = None
        self._scheduler: Optional[asyncio.Task] = None
        # Reminders for someone else that wait for them to accept, by (guild, creator, target).
        self._asks: Dict[Any, ConfirmView] = {}

    async def cog_load(self):
        """Initializes the language manager and starts delivering reminders (including missed ones)."""
        self.lang_manager = LanguageManager.get_instance(self.bot)
        self._wake = asyncio.Event()
        self._scheduler = asyncio.create_task(self._run_scheduler())

    async def cog_unload(self):
        """Stops the scheduler; stored reminders stay for the next start."""
        if self._scheduler is not None:
            self._scheduler.cancel()
            self._scheduler = None
        for view in list(self._asks.values()):
            view.stop()
        self._asks.clear()

    # ------------------------------------------------------------- delivery
    def _seconds_until_next(self, now: float) -> float:
        """Returns how long the scheduler may sleep before the next reminder is due."""
        pending = self.store.pending()
        if not pending:
            return self.MAX_SLEEP_SECONDS
        return min(max(0.0, pending[0].due_at - now), self.MAX_SLEEP_SECONDS)

    async def _run_scheduler(self) -> None:
        """Delivers due reminders, then sleeps until the next one or until a new one is set."""
        while True:
            try:
                await self._deliver_due(self._now())
                delay = self._seconds_until_next(self._now())
            except Exception as error:
                # The scheduler must outlive a failing round, or no reminder would ever be sent.
                self.logger.error("Reminder scheduler round failed", exc_info=True)
                await func.report_error(error, "reminder scheduler")
                delay = self.RETRY_DELAY_SECONDS
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=max(delay, 0.5))
            except asyncio.TimeoutError:
                continue
            self._wake.clear()

    async def _deliver_due(self, now: float) -> None:
        """Delivers every reminder that is due at ``now``."""
        for reminder in self.store.due(now):
            await self._deliver_one(reminder, now)

    async def _lookup_user(self, user_id: int) -> Any:
        """Returns a user object, or None when the user cannot be found."""
        user = self.bot.get_user(user_id)
        if user is not None:
            return user
        try:
            return await self.bot.fetch_user(user_id)
        except discord.HTTPException:
            self.logger.warning(f"remind: user {user_id} could not be fetched", exc_info=True)
            return None

    def _fallback_text(self, reminder: Reminder, mention: str) -> str:
        """The fixed, translated reminder used when the model cannot write one."""
        return self.lang_manager.translate(
            reminder.guild_id, "commands", "remind", "responses", "reminder_message", user=mention, message=reminder.message
        )

    async def _deliver_one(self, reminder: Reminder, now: float) -> None:
        """Writes and sends one due reminder, falling back to a DM and then to a retry."""
        channel = self.bot.get_channel(reminder.channel_id)
        target = await self._lookup_user(reminder.target_id)
        creator = await self._lookup_user(reminder.creator_id)
        mention = target.mention if target is not None else f"<@{reminder.target_id}>"

        text: Optional[str] = None
        if channel is not None:
            request = ReminderRequest(
                target_mention=mention,
                target_name=getattr(target, "display_name", None) or getattr(target, "name", None) or mention,
                creator_name=getattr(creator, "display_name", None) or "someone",
                text=reminder.message,
                created_at=datetime.fromtimestamp(reminder.created_at),
                now=datetime.fromtimestamp(now),
                seconds_late=max(0.0, now - reminder.due_at),
            )
            try:
                text = await compose_reminder(self.bot.orchestrator, self.bot, channel, request)
            except Exception as error:
                # The reminder must still be delivered, so the fixed template is used instead.
                self.logger.error(f"remind: the model could not write reminder {reminder.id}", exc_info=True)
                await func.report_error(error, f"remind: composing reminder {reminder.id}")
        if not text:
            text = self._fallback_text(reminder, mention)

        # Only the target may be pinged, whatever the reminder text or the model wrote.
        allowed = discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(id=reminder.target_id)])
        delivered = False
        if channel is not None:
            try:
                await channel.send(text, allowed_mentions=allowed)
                delivered = True
            except discord.HTTPException:
                self.logger.warning(f"remind: could not post reminder {reminder.id} in its channel", exc_info=True)
        if not delivered and target is not None:
            try:
                await target.send(text, allowed_mentions=allowed)
                delivered = True
            except discord.HTTPException:
                self.logger.warning(f"remind: could not DM reminder {reminder.id}", exc_info=True)

        anchor = reminder.anchor_at if reminder.anchor_at is not None else reminder.due_at
        next_due = next_occurrence(anchor, reminder.repeat, now)
        if delivered:
            if next_due is not None:
                self.store.reschedule(reminder.id, next_due)
            else:
                self.store.finish(reminder.id, "delivered")
            return
        attempts = self.store.postpone(reminder.id, until=now + self.RETRY_DELAY_SECONDS)
        if attempts >= self.MAX_DELIVERY_ATTEMPTS:
            if next_due is not None:
                # A repeating reminder skips this occurrence instead of stopping for good.
                self.store.reschedule(reminder.id, next_due)
                self.logger.error(f"remind: skipping this occurrence of reminder {reminder.id} after {attempts} attempts")
            else:
                self.store.finish(reminder.id, "failed")
                self.logger.error(f"remind: giving up on reminder {reminder.id} after {attempts} attempts")

    # -------------------------------------------------------------- setting
    async def _set_reminder_logic(self, channel, target_user, time_str: str, message: str, guild_id: str, interaction: Optional[discord.Interaction] = None, creator=None, repeat: str = "none"):
        """Core reminder logic shared by the slash command and the LLM tool.

        Args:
            channel: Where the reminder will be posted.
            target_user: Who to remind.
            time_str: When, as the user wrote it.
            message: What to remind about.
            guild_id: Guild ID (``"@me"`` in direct messages).
            interaction: The slash command interaction to answer, if any.
            creator: Who is setting the reminder (defaults to the target).
            repeat: ``"none"``, ``"daily"`` or ``"weekly"``.

        Returns:
            The confirmation or error text.
        """
        try:
            if not self.lang_manager:
                self.lang_manager = LanguageManager.get_instance(self.bot)

            async def reply(text: str) -> str:
                if interaction:
                    await interaction.edit_original_response(content=text)
                return text

            if interaction:
                await interaction.edit_original_response(content=self.lang_manager.translate(guild_id, "commands", "remind", "responses", "received"))

            if repeat not in REPEAT_CHOICES:
                repeat = "none"

            reminder_time = self.parse_time(time_str, guild_id)
            if reminder_time is None:
                return await reply(self.lang_manager.translate(guild_id, "commands", "remind", "responses", "invalid_format"))

            time_diff = reminder_time - datetime.now()
            if time_diff.total_seconds() <= 0:
                return await reply(self.lang_manager.translate(guild_id, "commands", "remind", "responses", "future_time_required"))
            if time_diff.total_seconds() > self.MAX_HORIZON_SECONDS:
                return await reply(self.lang_manager.translate(guild_id, "commands", "remind", "responses", "too_far"))

            creator_id = getattr(creator, "id", None) or getattr(target_user, "id", None)
            if self.store.count_pending(creator_id) >= self.max_pending_per_user:
                return await reply(self.lang_manager.translate(
                    guild_id, "commands", "remind", "responses", "limit_reached", limit=self.max_pending_per_user
                ))

            due_at = self._now() + time_diff.total_seconds()
            # A reminder for someone else is only set once they accept it: otherwise anyone could keep
            # pinging a member with reminders they never asked for.
            if target_user is not None and target_user.id != creator_id:
                return await reply(await self._ask_target(
                    channel, creator_id, target_user, message, due_at, repeat, guild_id
                ))

            return await reply(self._store_reminder(channel, creator_id, target_user, message, due_at, repeat, guild_id))

        except Exception as e:
            await func.report_error(e, f"An error occurred in setting reminder: {e}")
            error_msg = self.lang_manager.translate(
                guild_id, "commands", "remind", "responses", "error_setting", error=str(e)
            )
            if interaction:
                await interaction.edit_original_response(content=error_msg)
            return error_msg

    def _t(self, guild_id: str, key: str, **kwargs: Any) -> str:
        return self.lang_manager.translate(guild_id, "commands", "remind", "responses", key, **kwargs)

    def _store_reminder(
        self, channel: Any, creator_id: int, target_user: Any, message: str, due_at: float, repeat: str, guild_id: str
    ) -> str:
        """Saves a reminder and returns the confirmation text."""
        self.store.add(
            guild_id=guild_id,
            channel_id=channel.id,
            creator_id=creator_id,
            target_id=target_user.id,
            message=message,
            created_at=self._now(),
            due_at=due_at,
            repeat=repeat,
        )
        if self._wake is not None:
            self._wake.set()
        confirmation = self._t(
            guild_id, "confirm_setup",
            duration=self.format_timedelta(timedelta(seconds=max(due_at - self._now(), 0)), guild_id),
            user=getattr(target_user, "mention", None) or f"<@{target_user.id}>", message=message,
        )
        if repeat != "none":
            confirmation += " " + self.lang_manager.translate(guild_id, "commands", "remind", "repeat", repeat)
        return confirmation

    def _problem_for_others(self, channel: Any, creator_id: int, target_user: Any) -> Optional[str]:
        """Why a reminder from ``creator_id`` for ``target_user`` cannot be set, or None when it may be."""
        if self.max_pending_from_others <= 0:
            return "others_off"
        guild = getattr(channel, "guild", None)
        if guild is None or guild.get_member(target_user.id) is None:
            return "others_not_member"
        if self.store.count_pending(creator_id) >= self.max_pending_per_user:
            return "limit_reached"
        if self.store.count_from_others(target_user.id) >= self.max_pending_from_others:
            return "others_limit"
        return None

    def _limit_text(self, guild_id: str, problem: str) -> str:
        limit = self.max_pending_per_user if problem == "limit_reached" else self.max_pending_from_others
        return self._t(guild_id, problem, limit=limit)

    async def _ask_target(
        self, channel: Any, creator_id: int, target_user: Any, message: str, due_at: float, repeat: str, guild_id: str
    ) -> str:
        """Posts the reminder with Accept and Decline buttons only ``target_user`` can press.

        Returns:
            What the person setting it is told.
        """
        problem = self._problem_for_others(channel, creator_id, target_user)
        if problem is not None:
            return self._limit_text(guild_id, problem)
        # Each question pings the member, so how often one person may ask is limited (owner's rate_limits).
        limiter = getattr(self.bot, "rate_limiter", None)
        if limiter is not None:
            wait = limiter.hit("ask_others", creator_id)
            if wait:
                return self._t(guild_id, "ask_too_often", wait=format_wait(wait))

        target_id = target_user.id

        async def on_confirm() -> str:
            # Checked again: the limits may have filled, or the member left, while the question was open.
            later_problem = self._problem_for_others(channel, creator_id, target_user)
            if later_problem is not None:
                return self._limit_text(guild_id, later_problem)
            return self._store_reminder(channel, creator_id, target_user, message, due_at, repeat, guild_id)

        def text(key: str) -> str:
            return self._t(guild_id, key)

        view = ConfirmView(target_id, text, on_confirm, self._asks, (guild_id, creator_id, target_id))
        repeat_text = (
            " " + self.lang_manager.translate(guild_id, "commands", "remind", "repeat", repeat) if repeat != "none" else ""
        )
        content = self._t(
            guild_id, "ask_prompt", target=f"<@{target_id}>", creator=f"<@{creator_id}>",
            time=f"<t:{int(due_at)}:f>", message=_shorten(message),
        ) + repeat_text
        await ask(channel, content, view, allowed_mentions=discord.AllowedMentions(
            everyone=False, roles=False, users=[discord.Object(id=target_id)]
        ))
        return self._t(guild_id, "ask_sent", user=f"<@{target_id}>")

    @app_commands.command(name="remind", description="Sets a reminder")
    @app_commands.describe(
        time="When to remind (e.g., in 10 minutes, or at 2023-12-31 20:00:00)",
        message="The content of the reminder",
        user="The user to remind (optional, defaults to yourself)",
        repeat="Repeat the reminder every day or every week (optional)",
    )
    @app_commands.choices(repeat=[
        app_commands.Choice(name="Once", value="none"),
        app_commands.Choice(name="Every day", value="daily"),
        app_commands.Choice(name="Every week", value="weekly"),
    ])
    async def remind(self, interaction: discord.Interaction, time: str, message: str, user: discord.User = None, repeat: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer(ephemeral=True, thinking=True)

        guild_id = str(interaction.guild_id)
        target_user = user or interaction.user

        await self._set_reminder_logic(
            channel=interaction.channel,
            target_user=target_user,
            time_str=time,
            message=message,
            guild_id=guild_id,
            interaction=interaction,
            creator=interaction.user,
            repeat=repeat.value if repeat else "none",
        )

    # ----------------------------------------------------------- managing
    @app_commands.command(name="reminders", description="Lists your pending reminders")
    async def reminders(self, interaction: discord.Interaction):
        """Shows the reminders the user has set, with the ID needed to cancel one."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else "@me"
        pending = self.store.list_for_creator(interaction.user.id)
        # Reminders other people set for this member, so they can cancel them too.
        from_others = self.store.list_from_others(interaction.user.id)
        if not pending and not from_others:
            text = self.lang_manager.translate(guild_id, "commands", "remind", "responses", "list_empty")
        else:
            lines = []
            for title, reminders in (("list_title", pending), ("list_from_others_title", from_others)):
                if not reminders:
                    continue
                lines.append(self.lang_manager.translate(guild_id, "commands", "remind", "responses", title))
                for reminder in reminders:
                    line = self.lang_manager.translate(
                        guild_id, "commands", "remind", "responses", "list_item",
                        id=reminder.id, time=f"<t:{int(reminder.due_at)}:R>", message=reminder.message,
                    )
                    if reminder.creator_id != interaction.user.id:
                        line += " " + self.lang_manager.translate(
                            guild_id, "commands", "remind", "responses", "list_from", user=f"<@{reminder.creator_id}>"
                        )
                    if reminder.repeat != "none":
                        line += " " + self.lang_manager.translate(guild_id, "commands", "remind", "repeat", reminder.repeat)
                    lines.append(line)
            text = "\n".join(lines)
        await interaction.response.send_message(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="reminder_cancel", description="Cancels one of your reminders")
    @app_commands.describe(reminder_id="The ID shown by /reminders")
    async def reminder_cancel(self, interaction: discord.Interaction, reminder_id: int):
        """Cancels a pending reminder the user set or that someone set for them."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else "@me"
        key = "cancel_success" if self.store.cancel(reminder_id, interaction.user.id) else "cancel_not_found"
        text = self.lang_manager.translate(guild_id, "commands", "remind", "responses", key, id=reminder_id)
        await interaction.response.send_message(text, ephemeral=True)

    def _parse_relative_time_regex(self, time_str: str) -> Optional[datetime]:
        """使用正規表示式解析簡單的相對時間，例如 '10 分鐘後'"""
        # 支援的單位及其對應的 timedelta
        time_units = {
            'seconds': timedelta(seconds=1), 'second': timedelta(seconds=1), '秒': timedelta(seconds=1),
            'minutes': timedelta(minutes=1), 'minute': timedelta(minutes=1), '分鐘': timedelta(minutes=1),
            'hours': timedelta(hours=1),   'hour': timedelta(hours=1),   '小時': timedelta(hours=1),
            'days': timedelta(days=1),    'day': timedelta(days=1),    '天': timedelta(days=1),
            'weeks': timedelta(weeks=1),   'week': timedelta(weeks=1),   '週': timedelta(weeks=1),
        }
        
        # 正規表示式，匹配數字和單位
        pattern = r"(\d+)\s*(" + "|".join(time_units.keys()) + r")"
        match = re.search(pattern, time_str, re.IGNORECASE)
        
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            # 處理複數形式
            if not unit.endswith('s') and value > 1:
                unit += 's'
            if unit not in time_units: # 修正單數詞如 'day'
                 unit = unit.rstrip('s')

            delta = time_units.get(unit)
            if delta:
                return datetime.now() + (delta * value)
                
        return None

    def parse_time(self, time_str: str, guild_id: str = None) -> Optional[datetime]:
        """
        使用 dateparser 解析時間字串，並提供基於正規表示式的備用方案。
        """
        try:
            # 首先嘗試使用 dateparser
            parsed_time = dateparser.parse(
                time_str,
                settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': False}
            )
            if parsed_time:
                return parsed_time
        except Exception as e:
            # 如果 dateparser 失敗，繼續嘗試正規表示式
            self.logger.warning(f"Dateparser failed to parse '{time_str}': {e}")
            pass

        # 如果 dateparser 失敗或沒有回傳結果，嘗試使用正規表示式備用方案
        parsed_time = self._parse_relative_time_regex(time_str)
        if parsed_time:
            return parsed_time

        # 如果所有方法都失敗
        return None

    def format_timedelta(self, td: timedelta, guild_id: str = None) -> str:
        """格式化時間長度為本地化字串"""
        if not self.lang_manager:
            # 備用機制
            return self._format_time_fallback(td)
        
        total_seconds = int(td.total_seconds())
        
        # 計算各個時間單位
        years, remainder = divmod(total_seconds, 365 * 24 * 3600)
        months, remainder = divmod(remainder, 30 * 24 * 3600)
        weeks, remainder = divmod(remainder, 7 * 24 * 3600)
        days, remainder = divmod(remainder, 24 * 3600)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # 建立本地化時間格式
        parts = []
        time_components = [
            (years, "years"),
            (months, "months"),
            (weeks, "weeks"),
            (days, "days"),
            (hours, "hours"),
            (minutes, "minutes"),
            (seconds, "seconds")
        ]
        
        for value, unit_key in time_components:
            if value > 0:
                unit_text = self.lang_manager.translate(
                    guild_id, "commands", "remind", "time_units", unit_key
                )
                if unit_text:
                    parts.append(f"{value}{unit_text}")
        
        # 如果沒有任何時間單位，顯示0秒
        if not parts:
            unit_text = self.lang_manager.translate(
                guild_id, "commands", "remind", "time_units", "seconds"
            )
            parts.append(f"0{unit_text or '秒'}")
        
        return " ".join(parts)
    
    def _format_time_fallback(self, td: timedelta) -> str:
        """備用時間格式化機制（當翻譯系統不可用時）"""
        days, remainder = divmod(td.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{int(days)}天")
        if hours > 0:
            parts.append(f"{int(hours)}小時")
        if minutes > 0:
            parts.append(f"{int(minutes)}分鐘")
        if seconds > 0 or not parts:
            parts.append(f"{int(seconds)}秒")
        
        return " ".join(parts)

async def setup(bot):
    await bot.add_cog(ReminderCog(bot))
