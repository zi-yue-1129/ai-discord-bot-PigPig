"""Events (揪團): a sign-up message with Join / Maybe / Leave buttons and a reminder before it starts.

``/event create`` posts the event with its time and the people going. With a limit, people who
join once it is full wait in line and move up when someone leaves. Shortly before the start
(``remind`` minutes, 15 by default) the bot mentions everyone going in the event's channel.
The buttons keep working after a restart (persistent view, looked up by the message).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import dateparser
import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from function import func

from addons.visibility import audience_can_read, can_read, current_member

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
# How long the host has to confirm an event the AI proposed.
DRAFT_SECONDS = 180


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


@dataclass
class EventDraft:
    """An event the AI proposed for a member; it is only made once they press Confirm."""

    guild_id: int
    channel_id: int
    creator_id: int
    title: str
    starts_at: float
    capacity: int
    remind_minutes: int


class EventDraftView(discord.ui.View):
    """Confirm and Cancel buttons under an event the AI proposed; only its host may press them."""

    def __init__(self, cog: "EventsCog", draft: EventDraft, timeout: float = DRAFT_SECONDS) -> None:
        super().__init__(timeout=timeout)
        self.cog = cog
        self.draft = draft
        self.message: Any = None
        # Set before the first await of a press, so a second press can never make a second event.
        self.done = False
        for item, key in zip(self.children, ("draft_confirm", "draft_cancel")):
            item.label = cog._t(draft.guild_id, key)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.draft.creator_id:
            await interaction.response.send_message(self.cog._t(self.draft.guild_id, "draft_not_yours"), ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="✅", label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.confirm_draft(interaction, self)

    @discord.ui.button(emoji="✖️", label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.done:
            await interaction.response.send_message(self.cog._t(self.draft.guild_id, "draft_done"), ephemeral=True)
            return
        self.done = True
        self.stop()
        await interaction.response.edit_message(content=self.cog._t(self.draft.guild_id, "draft_cancelled"), view=None)

    async def on_timeout(self) -> None:
        if self.done or self.message is None:
            return
        self.done = True
        try:
            await self.message.edit(content=self.cog._t(self.draft.guild_id, "draft_expired"), view=None)
        except discord.HTTPException:
            pass


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
        # Acknowledge at once: waiting for the lock (e.g. behind a reminder) must not outlast Discord's 3 seconds.
        await interaction.response.defer()
        if event is None:
            await interaction.followup.send(self._t(guild_id, "event_gone"), ephemeral=True)
            return
        user_id = interaction.user.id

        async def show(event: Event, roster: Roster) -> None:
            try:
                await interaction.edit_original_response(embed=self.render(event, roster), view=self._localised_view(guild_id))
            except discord.HTTPException:
                # The answer is saved either way; the confirmation and the promotion notice still go out.
                self.logger.warning(f"events: could not update the message of event {event.id}", exc_info=True)

        problem, event, before, after = await self._apply_answer(event.id, user_id, status, show)
        if problem is not None:
            await interaction.followup.send(self._t(guild_id, problem), ephemeral=True)
            return
        await interaction.followup.send(self._answer_text(guild_id, user_id, status, after), ephemeral=True)
        promoted = [user for user in after.going if user in before.waiting]
        if promoted:
            await self._announce_promotion(interaction.channel, event, promoted)

    async def _apply_answer(
        self, event_id: int, user_id: int, status: Optional[str], show: Callable[[Event, Roster], Awaitable[None]]
    ) -> Tuple[Optional[str], Optional[Event], Optional[Roster], Optional[Roster]]:
        """Records going, maybe or leaving (``None``) under the event's lock, and shows the new
        roster with ``show`` when it changed.

        Returns:
            ``(problem, event, roster before, roster after)``; ``problem`` is "event_gone" or
            "event_started" when nothing was recorded.
        """
        async with self._lock(event_id):
            # Checked under the lock: a cancel may have finished, or the start passed, while this one waited.
            event = self.store.get(event_id)
            if event is None or event.status == CANCELLED:
                return "event_gone", None, None, None
            if event.starts_at <= self._now():
                return "event_started", None, None, None
            before = self.store.roster(event)
            if status is None:
                changed = self.store.leave(event.id, user_id)
            else:
                self.store.sign_up(event.id, user_id, status, self._now())
                changed = True
            after = self.store.roster(event)
            if changed:
                await show(event, after)
        return None, event, before, after

    async def answer_for_member(
        self, guild: discord.Guild, user_id: int, event_id: int, status: Optional[str]
    ) -> Tuple[Optional[str], Optional[Event], Optional[Roster]]:
        """Signs a member up (or out) of an event outside its buttons (the AI's ``join_event`` tool).

        The member must still be able to read the event's channel; an event they cannot read is
        "not_found", like for ``/event cancel``. Updates the event's message and tells anyone who
        moved up from the waiting list, in the event's channel.

        Returns:
            ``(problem, event, roster after)``; ``problem`` is a response key when nothing was recorded.
        """
        event = self.store.get(event_id)
        if event is None or event.guild_id != guild.id or event.status == CANCELLED:
            return "not_found", None, None
        member = await current_member(guild, user_id)
        channel = guild.get_channel_or_thread(event.channel_id)
        if member is None or not can_read(channel, member):
            return "not_found", None, None

        async def show(event: Event, roster: Roster) -> None:
            await self._refresh_message(event)

        problem, event, before, after = await self._apply_answer(event.id, user_id, status, show)
        if problem is not None:
            return problem, None, None
        promoted = [user for user in after.going if user in before.waiting]
        if promoted:
            await self._announce_promotion(channel, event, promoted)
        return None, event, after

    def _answer_text(self, guild_id: Any, user_id: int, status: Optional[str], roster: Roster) -> str:
        if user_id in roster.going:
            return self._t(guild_id, "you_are_going")
        if user_id in roster.waiting:
            return self._t(guild_id, "you_are_waiting", position=roster.waiting.index(user_id) + 1)
        if user_id in roster.maybe:
            return self._t(guild_id, "you_are_maybe")
        return self._t(guild_id, "you_left")

    def _shown_title(self, event: Event, channel: Any) -> str:
        """The event's title for a new post in ``channel``, or a link to the event when some people
        who see the channel may not read its history (the title is in an older message)."""
        if audience_can_read(channel):
            return event.title
        return self._untitled(event)

    def _untitled(self, event: Event) -> str:
        """The event named by its number and a link, for places where its title may not show."""
        link = f"https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id}"
        return self._t(event.guild_id, "untitled_event", id=event.id, link=link)

    async def _announce_promotion(self, channel: Any, event: Event, user_ids: List[int]) -> None:
        """Tells the people who moved up from the waiting list (and pings only them)."""
        text = self._t(event.guild_id, "promoted", title=self._shown_title(event, channel))
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

    def check_start(self, guild_id: int, creator_id: int, starts_at: float) -> Optional[str]:
        """Why an event of ``creator_id`` starting at ``starts_at`` cannot be made now (a response
        key, see ``problem_text``), or None when it can."""
        now = self._now()
        if starts_at <= now:
            return "past_time"
        if starts_at - now > MAX_HORIZON_SECONDS:
            return "too_far"
        if self.store.count_upcoming(guild_id, now, creator_id) >= MAX_UPCOMING_PER_USER:
            return "user_limit"
        if self.store.count_upcoming(guild_id, now) >= MAX_UPCOMING_PER_GUILD:
            return "guild_limit"
        return None

    def problem_text(self, guild_id: Any, key: str) -> str:
        limits = {"user_limit": MAX_UPCOMING_PER_USER, "guild_limit": MAX_UPCOMING_PER_GUILD}
        return self._t(guild_id, key, limit=limits[key]) if key in limits else self._t(guild_id, key)

    # ------------------------------------------------------------- drafts
    async def post_draft(
        self, channel: Any, creator: Any, title: str, time_text: str, capacity: int = 0, remind_minutes: int = 15
    ) -> Tuple[Optional[str], Optional[EventDraft]]:
        """Posts an event the AI proposed, with a Confirm button only ``creator`` may press.

        Nothing is saved until they press it (see ``confirm_draft``).

        Returns:
            ``(None, draft)``, or ``(problem, None)`` with a response key: "invalid_title",
            "invalid_limit", "invalid_remind", "invalid_time" or one of ``check_start``'s.
        """
        guild_id = channel.guild.id
        title = " ".join(str(title or "").split())
        if not 1 <= len(title) <= MAX_TITLE_LENGTH:
            return "invalid_title", None
        if not 0 <= int(capacity) <= MAX_CAPACITY:
            return "invalid_limit", None
        if not 0 <= int(remind_minutes) <= MAX_REMIND_MINUTES:
            return "invalid_remind", None
        starts = self.parse_time(str(time_text or ""))
        if starts is None:
            return "invalid_time", None
        draft = EventDraft(guild_id, channel.id, creator.id, title, starts.timestamp(), int(capacity), int(remind_minutes))
        problem = self.check_start(guild_id, creator.id, draft.starts_at)
        if problem is not None:
            return problem, None
        view = EventDraftView(self, draft)
        view.message = await channel.send(self.draft_text(draft), view=view, allowed_mentions=discord.AllowedMentions.none())
        return None, draft

    def draft_text(self, draft: EventDraft) -> str:
        when = f"<t:{int(draft.starts_at)}:F> (<t:{int(draft.starts_at)}:R>)"
        limit = str(draft.capacity) if draft.capacity else "∞"
        return self._t(
            draft.guild_id, "draft_prompt", host=f"<@{draft.creator_id}>", title=draft.title, when=when,
            limit=limit, minutes=draft.remind_minutes,
        )

    async def confirm_draft(self, interaction: discord.Interaction, view: EventDraftView) -> None:
        """Makes the drafted event and turns the draft message into the event's message."""
        draft = view.draft
        if view.done:
            await interaction.response.send_message(self._t(draft.guild_id, "draft_done"), ephemeral=True)
            return
        view.done = True
        view.stop()
        # The limits and the start are checked again: time passed and other events may have been made.
        problem = self.check_start(draft.guild_id, draft.creator_id, draft.starts_at)
        if problem is not None:
            await interaction.response.edit_message(content=self.problem_text(draft.guild_id, problem), view=None)
            return
        now = self._now()
        event_id = self.store.add(
            draft.guild_id, draft.channel_id, draft.creator_id, draft.title, draft.starts_at, draft.capacity,
            draft.remind_minutes, now,
        )
        self.store.sign_up(event_id, draft.creator_id, GOING, now)
        event = self.store.get(event_id)
        try:
            await interaction.response.edit_message(
                content=None,
                embed=self.render(event, self.store.roster(event)),
                view=self._localised_view(draft.guild_id),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException:
            # The draft still shows its (now dead) buttons and no event: take the event back.
            self.store.delete(event_id)
            raise
        self.store.set_message(event_id, interaction.message.id)
        if self._wake is not None:
            self._wake.set()

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
        problem = self.check_start(guild_id, interaction.user.id, starts_at)
        if problem is not None:
            await interaction.response.send_message(self.problem_text(guild_id, problem), ephemeral=True)
            return
        title = " ".join(title.split())
        event_id = self.store.add(guild_id, interaction.channel_id, interaction.user.id, title, starts_at, limit, remind, now)
        # The host is going to their own event.
        self.store.sign_up(event_id, interaction.user.id, GOING, now)
        event = self.store.get(event_id)
        try:
            callback = await interaction.response.send_message(
                embed=self.render(event, self.store.roster(event)),
                view=self._localised_view(guild_id),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException:
            # Nothing was posted: the event goes too.
            self.store.delete(event_id)
            raise
        # The message is posted from here on, so the event stays whatever happens next.
        message_id = getattr(callback, "message_id", None)
        if message_id is None:
            try:
                message_id = (await interaction.original_response()).id
            except discord.HTTPException:
                # Without its message the event's buttons and reminder cannot work: take it back.
                self.logger.warning(f"events: posted event {event_id} but could not look up its message", exc_info=True)
                self.store.delete(event_id)
                try:
                    await interaction.delete_original_response()
                except discord.HTTPException:
                    # It could not be removed either: at least its buttons go, and it says so.
                    try:
                        await interaction.edit_original_response(content=self._t(guild_id, "post_failed"), embed=None, view=None)
                    except discord.HTTPException:
                        self.logger.warning(
                            f"events: the announcement of event {event_id} in channel {interaction.channel_id} could not be"
                            " removed; a moderator may delete it",
                            exc_info=True,
                        )
                try:
                    await interaction.followup.send(self._t(guild_id, "post_failed"), ephemeral=True)
                except discord.HTTPException:
                    pass
                return
        self.store.set_message(event_id, message_id)
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
    def _event_channel(interaction: discord.Interaction, event: Event) -> Any:
        guild = interaction.guild
        return guild.get_channel_or_thread(event.channel_id) if guild is not None else None

    @classmethod
    def _can_see(cls, interaction: discord.Interaction, event: Event) -> bool:
        """Whether the interaction's member may read the event's channel (see ``addons.visibility``)."""
        return can_read(cls._event_channel(interaction, event), interaction.user)

    async def _may_cancel_now(self, interaction: discord.Interaction, event: Event) -> Optional[str]:
        """Checks the member as they are now (the interaction's member is a snapshot): None when they
        may still cancel, otherwise the reply. A member who cannot be found may not."""
        member = await current_member(interaction.guild, interaction.user.id)
        channel = self._event_channel(interaction, event)
        if member is None or not can_read(channel, member):
            return "not_found"
        if event.creator_id != member.id:
            permissions = getattr(channel, "permissions_for", None)
            try:
                manages = bool(permissions and getattr(permissions(member), "manage_events", False))
            except (AttributeError, TypeError, discord.ClientException):
                manages = False
            if not manages:
                return "not_yours"
        return None

    @event.command(name="cancel", description="Cancel an event you created")
    @app_commands.describe(event_id="The event number (shown under the event)")
    async def cancel(self, interaction: discord.Interaction, event_id: int) -> None:
        guild_id = interaction.guild_id
        event = self.store.get(event_id)
        # An event in a channel the member cannot read is "not found", so its title never shows.
        if event is None or event.guild_id != guild_id or event.status == CANCELLED or not self._can_see(interaction, event):
            await interaction.response.send_message(self._t(guild_id, "not_found"), ephemeral=True)
            return
        permissions = getattr(interaction, "permissions", None)
        if event.creator_id != interaction.user.id and not getattr(permissions, "manage_events", False):
            await interaction.response.send_message(self._t(guild_id, "not_yours"), ephemeral=True)
            return
        # Acknowledge at once: waiting for the lock and the message edit must not outlast Discord's 3 seconds.
        await interaction.response.defer(ephemeral=True)
        async with self._lock(event.id):
            # Checked again before anything changes: another cancel may have run while this one
            # waited, and the member's access or roles may have changed.
            event = self.store.get(event.id)
            refusal = "not_found" if event is None else await self._may_cancel_now(interaction, event)
            if refusal is not None:
                await interaction.followup.send(self._t(guild_id, refusal), ephemeral=True)
                return
            if not self.store.cancel(event.id):
                await interaction.followup.send(self._t(guild_id, "already_cancelled"), ephemeral=True)
                return
            event = self.store.get(event.id)
            await self._refresh_message(event)
        # The edit took a while: the title is shown only if the member may still read the channel.
        member = await current_member(interaction.guild, interaction.user.id)
        title = event.title if can_read(self._event_channel(interaction, event), member) else self._untitled(event)
        await interaction.followup.send(self._t(guild_id, "cancelled", title=title), ephemeral=True)

    # ------------------------------------------------------------- reminders
    async def _run_scheduler(self) -> None:
        """Sends due reminders, then sleeps until the next one or until an event is created."""
        # Before the bot is ready its channel cache is empty: every event would look like its channel was gone.
        await self.bot.wait_until_ready()
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
        only the people still waiting for their reminder, even if someone left and joined again.
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
            channel = await self._resolve_channel(event, now)
            if channel is None:
                return
            key = "reminder" if event.starts_at > now else "reminder_now"
            when = f"<t:{int(event.starts_at)}:R>"
            # Whether the title may be shown is decided again for every message, since the channel's
            # permissions can change between them; the groups leave room for the longer of both texts.
            longest = max(
                (self._t(event.guild_id, key, title=title, when=when) for title in (event.title, self._shown_title(event, None))),
                key=len,
            )
            for users in mention_groups(longest, going):
                prefix = self._t(event.guild_id, key, title=self._shown_title(event, channel), when=when)
                mentions = discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(u) for u in users])
                # Recorded before sending and taken back on failure: a crash in between can at worst
                # miss these mentions, never repeat them.
                self.store.mark_users_reminded(event.id, users)
                try:
                    await channel.send(mention_chunks(prefix, users)[0], allowed_mentions=mentions)
                except discord.HTTPException:
                    self.store.unmark_users_reminded(event.id, users)
                    self.logger.warning(f"events: reminder for event {event.id} failed", exc_info=True)
                    self._fail(event, now)
                    return
            self.store.mark_reminded(event.id)

    async def _resolve_channel(self, event: Event, now: float) -> Any:
        """The event's channel, fetched when it is not cached (e.g. an archived thread).

        Only a channel that no longer exists ends the reminder; other errors count as a failed attempt.
        """
        channel = self.bot.get_channel(event.channel_id)
        if channel is not None:
            return channel
        try:
            return await self.bot.fetch_channel(event.channel_id)
        except discord.NotFound:
            self.logger.info(f"events: channel of event {event.id} is gone; no reminder")
            self.store.mark_reminded(event.id)
        except discord.HTTPException:
            self.logger.warning(f"events: could not fetch the channel of event {event.id}", exc_info=True)
            self._fail(event, now)
        return None

    def _fail(self, event: Event, now: float) -> None:
        """Counts a failed reminder; after the last attempt the event is not tried again."""
        if self.store.record_failure(event.id, now + RETRY_DELAY_SECONDS) >= MAX_DELIVERY_ATTEMPTS:
            self.store.mark_reminded(event.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventsCog(bot))
