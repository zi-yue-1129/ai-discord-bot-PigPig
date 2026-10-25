"""Events (揪團): a sign-up message with Join / Maybe / Leave buttons and a reminder before it starts.

``/event create`` posts the event with its time and the people going. With a limit, people who
join once it is full wait in line and move up when someone leaves. Shortly before the start
(``remind`` minutes, 15 by default) the bot mentions everyone going in the event's channel.
The buttons keep working after a restart (persistent view, looked up by the message).
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import dateparser
import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from function import func

from .events_lib.store import CANCELLED, GOING, MAYBE, OPEN, Event, EventStore, Roster
from .language_manager import LanguageManager

EVENTS_DB_PATH = "data/events.db"
MAX_TITLE_LENGTH = 100
MAX_CAPACITY = 100
MAX_REMIND_MINUTES = 24 * 60
MAX_HORIZON_SECONDS = 180 * 24 * 3600
MAX_UPCOMING_PER_USER = 5
MAX_UPCOMING_PER_GUILD = 25
MAX_DELIVERY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 60
MAX_SLEEP_SECONDS = 30
# Embed field values are capped at 1024 characters; a mention is up to 22.
FIELD_LIMIT = 1024
MESSAGE_LIMIT = 2000


def mention_lines(user_ids: List[int], limit: int = FIELD_LIMIT, more: str = "+{count}") -> str:
    """Mentions joined by spaces, cut to fit ``limit`` with "+N" for the rest."""
    text = ""
    for index, user_id in enumerate(user_ids):
        piece = f"<@{user_id}>"
        rest = more.format(count=len(user_ids) - index)
        candidate = f"{text} {piece}".strip()
        # Room for the "+N" marker when more mentions follow.
        reserve = 0 if index == len(user_ids) - 1 else len(rest) + 1
        if len(candidate) + reserve > limit:
            return f"{text} {rest}".strip()
        text = candidate
    return text


def mention_groups(prefix: str, user_ids: List[int], limit: int = MESSAGE_LIMIT) -> List[List[int]]:
    """The people to mention in each message, so that ``prefix`` plus their mentions fits ``limit``."""
    groups: List[List[int]] = [[]]
    length = len(prefix)
    for user_id in user_ids:
        piece = len(f" <@{user_id}>")
        if groups[-1] and length + piece > limit:
            groups.append([])
            length = len(prefix)
        groups[-1].append(user_id)
        length += piece
    return groups


def mention_chunks(prefix: str, user_ids: List[int], limit: int = MESSAGE_LIMIT) -> List[str]:
    """``prefix`` followed by every mention, split into messages under ``limit`` characters."""
    return [prefix + "".join(f" <@{user_id}>" for user_id in users) for users in mention_groups(prefix, user_ids, limit)]


class EventView(discord.ui.View):
    """The buttons on every event message; the event is found by the message they are on."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def _answer(self, interaction: discord.Interaction, status: Optional[str]) -> None:
        # Looked up on each press, so messages posted before a reload reach the current cog.
        cog = self.bot.get_cog("EventsCog")
        if cog is not None:
            await cog.answer(interaction, status)

    @discord.ui.button(emoji="✅", label="Join", style=discord.ButtonStyle.success, custom_id="pigpig:event:join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._answer(interaction, GOING)

    @discord.ui.button(emoji="🤔", label="Maybe", style=discord.ButtonStyle.secondary, custom_id="pigpig:event:maybe")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._answer(interaction, MAYBE)

    @discord.ui.button(emoji="❌", label="Leave", style=discord.ButtonStyle.danger, custom_id="pigpig:event:leave")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._answer(interaction, None)


class EventsCog(commands.Cog):
    """Events people sign up for, with a reminder before they start."""

    event = app_commands.Group(name="event", description="Plan an event people can sign up for", guild_only=True)

    def __init__(self, bot: commands.Bot, store: Optional[EventStore] = None) -> None:
        self.bot = bot
        self.store = store or EventStore(EVENTS_DB_PATH)
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="events")
        self._now = time.time
        self._wake: Optional[asyncio.Event] = None
        self._scheduler: Optional[asyncio.Task] = None
        self.view = EventView(bot)
        # One update at a time per event, so the message always shows the latest roster.
        self._locks: Dict[int, asyncio.Lock] = {}

    async def cog_load(self) -> None:
        self.lang_manager = LanguageManager.get_instance(self.bot)
        self.bot.add_view(self.view)
        self._wake = asyncio.Event()
        self._scheduler = asyncio.create_task(self._run_scheduler())

    async def cog_unload(self) -> None:
        self.view.stop()
        if self._scheduler is not None:
            self._scheduler.cancel()
            self._scheduler = None

    def _t(self, guild_id: Any, key: str, **kwargs: Any) -> str:
        if self.lang_manager is None:
            return key
        return self.lang_manager.translate(str(guild_id), "commands", "events", "responses", key, **kwargs)

    def _lock(self, event_id: int) -> asyncio.Lock:
        return self._locks.setdefault(event_id, asyncio.Lock())

    # ------------------------------------------------------------- rendering
    def render(self, event: Event, roster: Roster) -> discord.Embed:
        guild_id = event.guild_id
        cancelled = event.status == CANCELLED
        title = f"📅 {event.title}" if not cancelled else f"~~{event.title}~~ ({self._t(guild_id, 'cancelled_tag')})"
        when = f"<t:{int(event.starts_at)}:F> (<t:{int(event.starts_at)}:R>)"
        embed = discord.Embed(
            title=title[:256],
            description=self._t(guild_id, "embed_description", when=when, host=f"<@{event.creator_id}>"),
            colour=discord.Colour.dark_grey() if cancelled else discord.Colour.blurple(),
        )
        more = self._t(guild_id, "and_more", count="{count}")
        going_name = self._t(guild_id, "going_field", count=len(roster.going))
        if event.capacity:
            going_name = self._t(guild_id, "going_field_limited", count=len(roster.going), limit=event.capacity)
        embed.add_field(name=going_name, value=mention_lines(roster.going, more=more) or "—", inline=False)
        if roster.waiting:
            embed.add_field(
                name=self._t(guild_id, "waiting_field", count=len(roster.waiting)),
                value=mention_lines(roster.waiting, more=more),
                inline=False,
            )
        if roster.maybe:
            embed.add_field(
                name=self._t(guild_id, "maybe_field", count=len(roster.maybe)),
                value=mention_lines(roster.maybe, more=more),
                inline=False,
            )
        embed.set_footer(text=self._t(guild_id, "embed_footer", id=event.id, minutes=event.remind_minutes))
        return embed

    def _localised_view(self, guild_id: Any) -> EventView:
        """A view with the same custom ids as the persistent one, labelled in the server's language."""
        view = EventView(self.bot)
        for item, key in zip(view.children, ("button_join", "button_maybe", "button_leave")):
            item.label = self._t(guild_id, key)
        return view

    async def _refresh_message(self, event: Event) -> None:
        """Shows the current roster on the event's message (when it still exists)."""
        channel = self.bot.get_channel(event.channel_id)
        if channel is None or event.message_id is None:
            return
        view = None if event.status == CANCELLED else self._localised_view(event.guild_id)
        try:
            message = channel.get_partial_message(event.message_id)
            await message.edit(embed=self.render(event, self.store.roster(event)), view=view)
        except discord.HTTPException:
            self.logger.warning(f"events: could not update the message of event {event.id}", exc_info=True)

    # -------------------------------------------------------------- buttons
    async def answer(self, interaction: discord.Interaction, status: Optional[str]) -> None:
        """Records a button press: going, maybe, or leaving (``None``)."""
        message_id = interaction.message.id if interaction.message else None
        event = self.store.by_message(message_id) if message_id else None
        guild_id = interaction.guild_id
        if event is None or event.status == CANCELLED:
            await interaction.response.send_message(self._t(guild_id, "event_gone"), ephemeral=True)
            return
        if event.starts_at <= self._now():
            await interaction.response.send_message(self._t(guild_id, "event_started"), ephemeral=True)
            return
        user_id = interaction.user.id
        async with self._lock(event.id):
            # Read again under the lock: a cancel may have finished while this press waited.
            event = self.store.get(event.id)
            if event is None or event.status == CANCELLED:
                await interaction.response.send_message(self._t(guild_id, "event_gone"), ephemeral=True)
                return
            before = self.store.roster(event)
            if status is None:
                changed = self.store.leave(event.id, user_id)
            else:
                self.store.sign_up(event.id, user_id, status, self._now())
                changed = True
            after = self.store.roster(event)
            if changed:
                await interaction.response.edit_message(embed=self.render(event, after), view=self._localised_view(guild_id))
            else:
                await interaction.response.defer()
        await interaction.followup.send(self._answer_text(guild_id, user_id, status, after), ephemeral=True)
        promoted = [user for user in after.going if user in before.waiting]
        if promoted:
            await self._announce_promotion(interaction.channel, event, promoted)

    def _answer_text(self, guild_id: Any, user_id: int, status: Optional[str], roster: Roster) -> str:
        if user_id in roster.going:
            return self._t(guild_id, "you_are_going")
        if user_id in roster.waiting:
            return self._t(guild_id, "you_are_waiting", position=roster.waiting.index(user_id) + 1)
        if user_id in roster.maybe:
            return self._t(guild_id, "you_are_maybe")
        return self._t(guild_id, "you_left")

    async def _announce_promotion(self, channel: Any, event: Event, user_ids: List[int]) -> None:
        """Tells the people who moved up from the waiting list (and pings only them)."""
        text = self._t(event.guild_id, "promoted", title=event.title)
        try:
            for chunk in mention_chunks(text, user_ids):
                await channel.send(
                    chunk, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(u) for u in user_ids])
                )
        except discord.HTTPException:
            self.logger.warning(f"events: could not announce promotion for event {event.id}", exc_info=True)

    # ------------------------------------------------------------- commands
    def parse_time(self, text: str) -> Optional[datetime]:
        """The time ``text`` names, read like reminder times (``明天 20:00``, ``30分鐘後``, ``tomorrow 8pm``)."""
        reminders = self.bot.get_cog("ReminderCog") if hasattr(self.bot, "get_cog") else None
        if reminders is not None and hasattr(reminders, "parse_time"):
            return reminders.parse_time(text)
        try:
            return dateparser.parse(text, settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False})
        except Exception:
            return None

    @event.command(name="create", description="Post an event people can join")
    @app_commands.describe(
        title="What the event is",
        time="When it starts (e.g. tomorrow 20:00, in 2 hours)",
        limit="Most people who can join; others wait in line (0 = no limit)",
        remind="Minutes before the start to remind everyone going (default 15)",
    )
    async def create(
        self,
        interaction: discord.Interaction,
        title: app_commands.Range[str, 1, MAX_TITLE_LENGTH],
        time: str,
        limit: app_commands.Range[int, 0, MAX_CAPACITY] = 0,
        remind: app_commands.Range[int, 0, MAX_REMIND_MINUTES] = 15,
    ) -> None:
        guild_id, now = interaction.guild_id, self._now()
        starts = self.parse_time(time)
        if starts is None:
            await interaction.response.send_message(self._t(guild_id, "invalid_time"), ephemeral=True)
            return
        starts_at = starts.timestamp()
        if starts_at <= now:
            await interaction.response.send_message(self._t(guild_id, "past_time"), ephemeral=True)
            return
        if starts_at - now > MAX_HORIZON_SECONDS:
            await interaction.response.send_message(self._t(guild_id, "too_far"), ephemeral=True)
            return
        if self.store.count_upcoming(guild_id, now, interaction.user.id) >= MAX_UPCOMING_PER_USER:
            await interaction.response.send_message(self._t(guild_id, "user_limit", limit=MAX_UPCOMING_PER_USER), ephemeral=True)
            return
        if self.store.count_upcoming(guild_id, now) >= MAX_UPCOMING_PER_GUILD:
            await interaction.response.send_message(self._t(guild_id, "guild_limit", limit=MAX_UPCOMING_PER_GUILD), ephemeral=True)
            return
        title = " ".join(title.split())
        event_id = self.store.add(guild_id, interaction.channel_id, interaction.user.id, title, starts_at, limit, remind, now)
        # The host is going to their own event.
        self.store.sign_up(event_id, interaction.user.id, GOING, now)
        event = self.store.get(event_id)
        try:
            await interaction.response.send_message(
                embed=self.render(event, self.store.roster(event)),
                view=self._localised_view(guild_id),
                allowed_mentions=discord.AllowedMentions.none(),
            )
            message = await interaction.original_response()
        except discord.HTTPException:
            self.store.delete(event_id)
            raise
        self.store.set_message(event_id, message.id)
        if self._wake is not None:
            self._wake.set()

    @event.command(name="list", description="Show this server's upcoming events")
    async def list_events(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        # Events in channels the member cannot see stay hidden from them.
        events = [event for event in self.store.upcoming(guild_id, self._now()) if self._can_see(interaction, event)]
        if not events:
            await interaction.response.send_message(self._t(guild_id, "none_upcoming"), ephemeral=True)
            return
        lines = []
        for event in events:
            roster = self.store.roster(event)
            link = f"https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id}"
            lines.append(
                self._t(
                    guild_id, "list_line", id=event.id, title=event.title, when=f"<t:{int(event.starts_at)}:R>",
                    going=len(roster.going), link=link,
                )
            )
        text = "\n".join(lines)
        if len(text) > MESSAGE_LIMIT:
            text = text[: MESSAGE_LIMIT - 1] + "…"
        await interaction.response.send_message(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @staticmethod
    def _can_see(interaction: discord.Interaction, event: Event) -> bool:
        """Whether the member may see the event's channel: never for a private thread, whose
        permissions are inherited from its parent although only its members can read it."""
        guild = interaction.guild
        channel = guild.get_channel_or_thread(event.channel_id) if guild is not None else None
        if channel is None or getattr(channel, "type", None) == discord.ChannelType.private_thread:
            return False
        try:
            permissions = channel.permissions_for(interaction.user)
        except (AttributeError, TypeError, discord.ClientException):
            return False  # e.g. a thread whose parent is not cached: left out, never leaked
        return bool(permissions.view_channel and permissions.read_message_history)

    @event.command(name="cancel", description="Cancel an event you created")
    @app_commands.describe(event_id="The event number (shown under the event)")
    async def cancel(self, interaction: discord.Interaction, event_id: int) -> None:
        guild_id = interaction.guild_id
        event = self.store.get(event_id)
        if event is None or event.guild_id != guild_id or event.status == CANCELLED:
            await interaction.response.send_message(self._t(guild_id, "not_found"), ephemeral=True)
            return
        permissions = getattr(interaction, "permissions", None)
        if event.creator_id != interaction.user.id and not getattr(permissions, "manage_events", False):
            await interaction.response.send_message(self._t(guild_id, "not_yours"), ephemeral=True)
            return
        async with self._lock(event.id):
            self.store.cancel(event.id)
            event = self.store.get(event.id)
            await self._refresh_message(event)
        await interaction.response.send_message(self._t(guild_id, "cancelled", title=event.title), ephemeral=True)

    # ------------------------------------------------------------- reminders
    async def _run_scheduler(self) -> None:
        """Sends due reminders, then sleeps until the next one or until an event is created."""
        while True:
            try:
                await self._deliver_due(self._now())
                upcoming = self.store.next_reminder_at()
                delay = MAX_SLEEP_SECONDS if upcoming is None else min(max(0.0, upcoming - self._now()), MAX_SLEEP_SECONDS)
            except Exception as error:
                self.logger.error("Event reminder round failed", exc_info=True)
                await func.report_error(error, "event reminders")
                delay = RETRY_DELAY_SECONDS
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=max(delay, 0.5))
            except asyncio.TimeoutError:
                continue
            self._wake.clear()

    async def _deliver_due(self, now: float) -> None:
        for event in self.store.due_reminders(now):
            await self._remind(event, now)

    async def _remind(self, event: Event, now: float) -> None:
        """Mentions everyone going; marks the event reminded only once every message was sent.

        Each message records whom it mentioned, so a retry after a failure (or a restart) mentions
        only the people still waiting for their reminder.
        """
        async with self._lock(event.id):
            # Read again under the lock: the event may have been cancelled since the due query.
            event = self.store.get(event.id)
            if event is None or event.status != OPEN:
                return
            reminded = set(self.store.reminded_users(event.id))
            going = [user for user in self.store.roster(event).going if user not in reminded]
            if not going or event.starts_at <= now - 3600:
                # Nobody (left) to remind, or the bot was off long past the start.
                self.store.mark_reminded(event.id)
                return
            channel = self.bot.get_channel(event.channel_id)
            if channel is None:
                self._fail(event, now)
                return
            key = "reminder" if event.starts_at > now else "reminder_now"
            prefix = self._t(event.guild_id, key, title=event.title, when=f"<t:{int(event.starts_at)}:R>")
            for users in mention_groups(prefix, going):
                mentions = discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(u) for u in users])
                try:
                    await channel.send(mention_chunks(prefix, users)[0], allowed_mentions=mentions)
                except discord.HTTPException:
                    self.logger.warning(f"events: reminder for event {event.id} failed", exc_info=True)
                    self._fail(event, now)
                    return
                self.store.mark_users_reminded(event.id, users)
            self.store.mark_reminded(event.id)

    def _fail(self, event: Event, now: float) -> None:
        """Counts a failed reminder; after the last attempt the event is not tried again."""
        if self.store.record_failure(event.id, now + RETRY_DELAY_SECONDS) >= MAX_DELIVERY_ATTEMPTS:
            self.store.mark_reminded(event.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventsCog(bot))
