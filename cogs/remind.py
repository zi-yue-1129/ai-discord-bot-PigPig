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

from typing import Any, Optional
from .language_manager import LanguageManager
from .remind_lib.store import Reminder, ReminderStore
from function import func
from addons.logging import get_logger
from llm.reminder_writer import LATE_THRESHOLD_SECONDS, ReminderRequest, compose_reminder

REMINDER_DB_PATH = "data/reminders.db"


class ReminderCog(commands.Cog):
    """Sets reminders and, when each falls due, has the model write it from the recent chat."""

    MAX_PENDING_PER_USER = 20
    MAX_HORIZON_SECONDS = 365 * 24 * 3600
    MAX_DELIVERY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 60
    MAX_SLEEP_SECONDS = 30

    def __init__(self, bot):
        self.bot = bot
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="remind")
        self.store = ReminderStore(REMINDER_DB_PATH)
        self._now = time.time
        self._wake: Optional[asyncio.Event] = None
        self._scheduler: Optional[asyncio.Task] = None

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

        if delivered:
            self.store.finish(reminder.id, "delivered")
            return
        attempts = self.store.postpone(reminder.id, until=now + self.RETRY_DELAY_SECONDS)
        if attempts >= self.MAX_DELIVERY_ATTEMPTS:
            self.store.finish(reminder.id, "failed")
            self.logger.error(f"remind: giving up on reminder {reminder.id} after {attempts} attempts")

    # -------------------------------------------------------------- setting
    async def _set_reminder_logic(self, channel, target_user, time_str: str, message: str, guild_id: str, interaction: Optional[discord.Interaction] = None, creator=None):
        """Core reminder logic shared by the slash command and the LLM tool.

        Args:
            channel: Where the reminder will be posted.
            target_user: Who to remind.
            time_str: When, as the user wrote it.
            message: What to remind about.
            guild_id: Guild ID (``"@me"`` in direct messages).
            interaction: The slash command interaction to answer, if any.
            creator: Who is setting the reminder (defaults to the target).

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

            reminder_time = self.parse_time(time_str, guild_id)
            if reminder_time is None:
                return await reply(self.lang_manager.translate(guild_id, "commands", "remind", "responses", "invalid_format"))

            time_diff = reminder_time - datetime.now()
            if time_diff.total_seconds() <= 0:
                return await reply(self.lang_manager.translate(guild_id, "commands", "remind", "responses", "future_time_required"))
            if time_diff.total_seconds() > self.MAX_HORIZON_SECONDS:
                return await reply(self.lang_manager.translate(guild_id, "commands", "remind", "responses", "too_far"))

            creator_id = getattr(creator, "id", None) or getattr(target_user, "id", None)
            if self.store.count_pending(creator_id) >= self.MAX_PENDING_PER_USER:
                return await reply(self.lang_manager.translate(
                    guild_id, "commands", "remind", "responses", "limit_reached", limit=self.MAX_PENDING_PER_USER
                ))

            mention_safe = getattr(target_user, "mention", None)
            if not mention_safe:
                self.logger.warning(f"remind: target_user 無法取得 mention (target_user={target_user}, channel={getattr(channel,'id',None)}, interaction_user={getattr(interaction,'user',None)})")
                if target_user and getattr(target_user, "id", None):
                    mention_safe = f"<@{target_user.id}>"
                else:
                    mention_safe = self.lang_manager.translate(guild_id, "commands", "remind", "responses", "fallback_user")

            now = self._now()
            self.store.add(
                guild_id=guild_id,
                channel_id=channel.id,
                creator_id=creator_id,
                target_id=target_user.id,
                message=message,
                created_at=now,
                due_at=now + time_diff.total_seconds(),
            )
            if self._wake is not None:
                self._wake.set()

            return await reply(self.lang_manager.translate(
                guild_id, "commands", "remind", "responses", "confirm_setup",
                duration=self.format_timedelta(time_diff, guild_id), user=mention_safe, message=message,
            ))

        except Exception as e:
            await func.report_error(e, f"An error occurred in setting reminder: {e}")
            error_msg = self.lang_manager.translate(
                guild_id, "commands", "remind", "responses", "error_setting", error=str(e)
            )
            if interaction:
                await interaction.edit_original_response(content=error_msg)
            return error_msg

    @app_commands.command(name="remind", description="Sets a reminder")
    @app_commands.describe(
        time="When to remind (e.g., in 10 minutes, or at 2023-12-31 20:00:00)",
        message="The content of the reminder",
        user="The user to remind (optional, defaults to yourself)"
    )
    async def remind(self, interaction: discord.Interaction, time: str, message: str, user: discord.User = None):
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
        )

    # ----------------------------------------------------------- managing
    @app_commands.command(name="reminders", description="Lists your pending reminders")
    async def reminders(self, interaction: discord.Interaction):
        """Shows the reminders the user has set, with the ID needed to cancel one."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else "@me"
        pending = self.store.list_for_creator(interaction.user.id)
        if not pending:
            text = self.lang_manager.translate(guild_id, "commands", "remind", "responses", "list_empty")
        else:
            lines = [self.lang_manager.translate(guild_id, "commands", "remind", "responses", "list_title")]
            for reminder in pending:
                lines.append(self.lang_manager.translate(
                    guild_id, "commands", "remind", "responses", "list_item",
                    id=reminder.id, time=f"<t:{int(reminder.due_at)}:R>", message=reminder.message,
                ))
            text = "\n".join(lines)
        await interaction.response.send_message(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="reminder_cancel", description="Cancels one of your reminders")
    @app_commands.describe(reminder_id="The ID shown by /reminders")
    async def reminder_cancel(self, interaction: discord.Interaction, reminder_id: int):
        """Cancels a pending reminder the user set."""
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
