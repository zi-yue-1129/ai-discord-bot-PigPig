"""Community features: welcoming new members, birthdays, yearly join anniversaries, the weekly recap
and achievement announcements.

Every feature is off until a server admin turns it on with ``/community``; the bot owner
sets the limits in the ``community:`` block of base.yaml. Messages are written by the
model in the bot's voice, with a fixed translated text whenever the model is unavailable,
over budget, or the server is being raided.
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Tuple

import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from addons.settings import base_config
from addons.tokens import tokens
from function import func
from llm.announcement_writer import compose_announcement

from .community_lib.dates import (
    anniversary_years,
    birthdays_on,
    is_valid_birthday,
    local_now,
    parse_timezone,
    upcoming_birthdays,
)
from .community_lib.joins import JoinTracker
from .community_lib.limits import CommunityLimits
from .community_lib.recap import RecapBuilder, format_recap, recap_facts, recap_week_due
from .community_lib.store import CommunityStore, GuildSettings
from .language_manager import LanguageManager

COMMUNITY_DB_PATH = "data/community.db"
# Discord refuses longer messages.
MESSAGE_LIMIT = 2000
# A failed daily job or role removal waits longer after each failure, up to this long.
MAX_RETRY_SECONDS = 3600
# A birthday role must not carry any of these: the bot hands it out without a moderator.
_UNSAFE_ROLE_PERMISSIONS = discord.Permissions.elevated() | discord.Permissions(
    mute_members=True, deafen_members=True, move_members=True, manage_nicknames=True, mention_everyone=True
)

_WELCOME_TASK = (
    "New members just joined this Discord server. Welcome them warmly and briefly (one to three "
    "sentences), mention each of them, and weave in the admin's note if there is one."
)
_BIRTHDAY_TASK = "Today is the birthday of the members below. Wish them a happy birthday, mentioning each of them."
_ANNIVERSARY_TASK = (
    "Today is the yearly anniversary of the day the members below joined this server. Congratulate "
    "them and say how many years each has been here, mentioning each of them."
)
_WEEKLY_TASK = (
    "Write this week's server news report: a funny, warm news-style paragraph of at most {chars} "
    "characters about the numbers below. Use names as given, without mentions; do not list every number."
)
_WEEKDAYS = [
    app_commands.Choice(name=name, value=index)
    for index, name in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
]


class CommunityCog(commands.Cog):
    """Welcomes members and celebrates birthdays and join anniversaries."""

    CHECK_SECONDS = 300
    UPCOMING_DAYS = 30

    community = app_commands.Group(
        name="community",
        description="Server community features: welcomes, birthdays and anniversaries",
        guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True),
    )
    birthday = app_commands.Group(name="birthday", description="Your birthday on this server", guild_only=True)

    def __init__(self, bot: commands.Bot, store: Optional[CommunityStore] = None) -> None:
        self.bot = bot
        self.store = store or CommunityStore(COMMUNITY_DB_PATH)
        self.limits = CommunityLimits.from_config(getattr(base_config, "community", {}))
        self.joins = JoinTracker(
            self.limits.welcome_burst_threshold, self.limits.welcome_burst_seconds, self.limits.welcome_max_ai_per_hour
        )
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="community")
        self._now = time.time
        self._scheduler: Optional[asyncio.Task] = None
        self._flushes: Dict[int, asyncio.Task] = {}
        # key -> (failures so far, time of the next try); see _may_retry and _failed.
        self._retries: Dict[Tuple[Any, ...], Tuple[int, float]] = {}

    async def cog_load(self) -> None:
        self.lang_manager = LanguageManager.get_instance(self.bot)
        self._scheduler = asyncio.create_task(self._run_scheduler())

    async def cog_unload(self) -> None:
        for task in [self._scheduler, *self._flushes.values()]:
            if task is not None:
                task.cancel()
        self._scheduler = None
        self._flushes.clear()

    # ------------------------------------------------------------ helpers
    def _t(self, guild_id: Any, key: str, **kwargs: Any) -> str:
        """Translates a community response for a guild."""
        if self.lang_manager is None:
            return key
        return self.lang_manager.translate(str(guild_id), "commands", "community", "responses", key, **kwargs)

    def _channel_for(self, guild: discord.Guild, settings: GuildSettings, channel_id: Optional[int] = None) -> Any:
        """Returns the channel to post in: the feature's own, the announcement channel, or the system channel."""
        for candidate in (channel_id, settings.announce_channel_id):
            if candidate:
                channel = guild.get_channel(candidate)
                if channel is not None:
                    return channel
        return guild.system_channel

    def _local_now(self, settings: GuildSettings) -> datetime:
        return local_now(datetime.fromtimestamp(self._now(), timezone.utc), settings.timezone, self.limits.default_timezone)

    async def _write(self, channel: Any, task: str, facts: str, mentions: Sequence[str], use_ai: bool) -> Optional[str]:
        """Has the model write an announcement; None when AI is off for it or the model fails."""
        if not use_ai or getattr(self.bot, "orchestrator", None) is None:
            return None
        try:
            return await compose_announcement(self.bot.orchestrator, self.bot, channel, task, facts, mentions)
        except Exception as error:
            # The fixed text is posted instead, so the failure is only reported.
            self.logger.error("community: the model could not write an announcement", exc_info=True)
            await func.report_error(error, "community: composing an announcement")
            return None

    async def _send(self, channel: Any, text: str, members: Sequence[Any]) -> bool:
        """Posts ``text`` (split into several messages when too long), allowing pings only for ``members``.

        Returns False when any part could not be posted, so a job is retried rather than leaving
        some members out (a retry may repeat the parts that did go out).
        """
        allowed = discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(id=m.id) for m in members])
        for chunk in split_message(text):
            try:
                await channel.send(chunk, allowed_mentions=allowed)
            except discord.HTTPException:
                self.logger.warning(f"community: could not post in channel {getattr(channel, 'id', None)}", exc_info=True)
                return False
        return True

    @staticmethod
    def _pick_emoji(guild: discord.Guild) -> str:
        """Returns one of the guild's usable custom emojis as text, or an empty string."""
        emojis = [emoji for emoji in getattr(guild, "emojis", []) if getattr(emoji, "available", True)]
        return str(random.choice(emojis)) if emojis else ""

    # ------------------------------------------------------------ welcome
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        settings = self.store.get_settings(member.guild.id)
        if not settings.welcome_enabled:
            return
        if self.joins.add(member.guild.id, member, self._now()):
            self._flushes[member.guild.id] = asyncio.create_task(self._flush_after_delay(member.guild))

    async def _flush_after_delay(self, guild: discord.Guild) -> None:
        try:
            await asyncio.sleep(self.limits.welcome_batch_seconds)
            await self.welcome(guild, self.joins.take_batch(guild.id))
        except asyncio.CancelledError:
            raise
        except Exception as error:
            await func.report_error(error, f"community: welcoming members in guild {guild.id}")
        finally:
            # A newer batch may have been scheduled meanwhile; only drop our own entry.
            if self._flushes.get(guild.id) is asyncio.current_task():
                del self._flushes[guild.id]

    async def welcome(self, guild: discord.Guild, members: List[discord.Member], *, preview_channel: Any = None) -> Optional[str]:
        """Welcomes a batch of new members; returns the posted text (None when nothing was posted).

        Args:
            guild: The guild they joined.
            members: The new members.
            preview_channel: When given, the text is only built (for /community welcome_test), not posted.
        """
        if not members:
            return None
        settings = self.store.get_settings(guild.id)
        channel = preview_channel or self._channel_for(guild, settings, settings.welcome_channel_id)
        if channel is None:
            return None
        now = self._now()
        mentions = [member.mention for member in members]
        raid = self.joins.is_raid(guild.id, now)
        text = None
        if not raid and self.joins.use_ai(guild.id, now):
            emoji = self._pick_emoji(guild)
            facts = "\n".join(
                line
                for line in [
                    f"Server: <<<{guild.name}>>> (now {guild.member_count} members).",
                    "New members: " + ", ".join(f"<<<{m.display_name}>>> (mention as {m.mention})" for m in members),
                    f"Admin's note to include: <<<{settings.welcome_note}>>>" if settings.welcome_note else "",
                    f"You may use this server emoji: {emoji}" if emoji else "",
                ]
                if line
            )
            text = await self._write(channel, _WELCOME_TASK, facts, mentions, use_ai=True)
        if not text:
            if len(members) == 1:
                text = self._t(guild.id, "welcome_single", mention=mentions[0], guild=guild.name, count=guild.member_count)
            else:
                text = self._t(guild.id, "welcome_many", mentions=" ".join(mentions), guild=guild.name)
            if settings.welcome_note:
                text = f"{text}\n{settings.welcome_note}"
        if preview_channel is not None:
            return text
        return text if await self._send(channel, text, members) else None

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.bot:
            return
        settings = self.store.get_settings(member.guild.id)
        if not (settings.welcome_enabled and settings.farewell_enabled):
            return
        channel = self._channel_for(member.guild, settings, settings.welcome_channel_id)
        if channel is not None:
            await self._send(channel, self._t(member.guild.id, "farewell", name=member.display_name), [])

    # ------------------------------------------------------------ daily jobs
    async def _run_scheduler(self) -> None:
        """Runs the daily jobs every few minutes; each runs once per guild per local day."""
        await self.bot.wait_until_ready()
        while True:
            try:
                await self.run_daily_jobs()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                await func.report_error(error, "community: daily jobs")
            await asyncio.sleep(self.CHECK_SECONDS)

    async def run_daily_jobs(self) -> None:
        """Posts the birthday, anniversary and weekly recap messages that are due, and takes back expired birthday roles."""
        await self._remove_expired_birthday_roles()
        for settings in self.store.guilds_with_daily_jobs():
            guild = self.bot.get_guild(settings.guild_id)
            if guild is None:
                continue
            local = self._local_now(settings)
            if settings.weekly_enabled:
                monday = recap_week_due(local, settings.weekly_day, settings.weekly_hour)
                if monday is not None:
                    end = min(local, monday + timedelta(days=7))
                    await self._run_job(
                        guild.id, "weekly", monday.date().isoformat(),
                        lambda: self._weekly_job(guild, settings, monday, end),
                    )
            if local.hour < settings.birthday_hour:
                continue
            today = local.date().isoformat()
            if settings.birthday_enabled:
                await self._run_job(guild.id, "birthday", today, lambda: self.celebrate_birthdays(guild, settings, local))
                if settings.birthday_role_id:
                    await self._run_job(
                        guild.id, "birthday_role", today,
                        lambda: self._give_birthday_role(guild, settings.birthday_role_id, self._birthday_members(guild, local), local),
                    )
            if settings.anniversary_enabled:
                await self._run_job(guild.id, "anniversary", today, lambda: self.celebrate_anniversaries(guild, settings, local))

    async def _run_job(self, guild_id: int, job: str, period: str, run: Callable[[], Awaitable[bool]]) -> None:
        """Runs a job once per period.

        The job is only marked done once ``run`` returns True. A failure (e.g. a Discord outage or
        no permission to post) is retried, waiting longer each time (see ``_failed``), for as long
        as the period is due; it is never marked done without having run.
        """
        key = ("job", guild_id, job, period)
        if self.store.has_run(guild_id, job, period) or not self._may_retry(key):
            return
        try:
            done = await run()
        except asyncio.CancelledError:
            raise
        except discord.HTTPException:
            self.logger.warning(f"community: the {job} job failed in guild {guild_id}", exc_info=True)
            done = False
        except Exception as error:
            await func.report_error(error, f"community: the {job} job in guild {guild_id}")
            done = False
        if done:
            self._retries.pop(key, None)
            self.store.claim_run(guild_id, job, period)
        else:
            self._failed(key)

    def _may_retry(self, key: Tuple[Any, ...]) -> bool:
        """Whether something that failed before (or never failed) may be tried now."""
        entry = self._retries.get(key)
        return entry is None or self._now() >= entry[1]

    def _failed(self, key: Tuple[Any, ...]) -> int:
        """Records a failure; the next try waits one check, then twice as long each time, up to an hour.

        Returns:
            How many times it has failed in a row.
        """
        failures = self._retries.get(key, (0, 0.0))[0] + 1
        wait = min(self.CHECK_SECONDS * 2 ** (failures - 1), MAX_RETRY_SECONDS)
        self._retries[key] = (failures, self._now() + wait)
        return failures

    def _birthday_members(self, guild: discord.Guild, local: datetime) -> List[discord.Member]:
        """The members (not bots) whose birthday is on ``local``'s day, up to the mention limit.

        Members hidden with ``/leaderboard optout`` are left out, so they are neither named in the
        greeting nor marked by the birthday role. When the opt-out list cannot be read this raises,
        and the job is retried: nobody is named while it is unknown who is hidden.
        """
        hidden = self.store.read_optouts(guild.id)
        ids = [user_id for user_id in birthdays_on(local.date(), self.store.birthdays(guild.id)) if user_id not in hidden]
        members = [m for m in (guild.get_member(user_id) for user_id in ids) if m is not None and not m.bot]
        return members[: self.limits.birthday_max_mentions]

    async def celebrate_birthdays(self, guild: discord.Guild, settings: GuildSettings, local: datetime) -> bool:
        """Posts one message for everyone whose birthday is today; False when it could not be posted.

        With nowhere to post yet it also gives False, so a channel set later that day still gets it.
        """
        members = self._birthday_members(guild, local)
        if not members:
            return True
        channel = self._channel_for(guild, settings)
        if channel is None:
            return False
        mentions = [m.mention for m in members]
        facts = "Birthday members: " + ", ".join(f"<<<{m.display_name}>>> (mention as {m.mention})" for m in members)
        text = await self._write(channel, _BIRTHDAY_TASK, facts, mentions, self.limits.birthday_use_ai)
        return await self._send(channel, text or self._t(guild.id, "birthday", mentions=" ".join(mentions)), members)

    async def _give_birthday_role(
        self, guild: discord.Guild, role_id: int, members: Sequence[discord.Member], local: datetime
    ) -> bool:
        """Gives the birthday role until midnight; False when it could not be given to someone.

        Members who already have the role keep it afterwards: only roles the bot gave are taken back.
        """
        role = guild.get_role(role_id)
        if role is None:
            return True
        # Checked again here: the role or its permissions may have changed since it was chosen.
        problem = self._unsafe_birthday_role(guild, role)
        if problem:
            self.logger.warning(f"community: not giving birthday role {role.id} in guild {guild.id} ({problem})")
            return True
        midnight = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        given_all = True
        for member in members:
            if any(r.id == role.id for r in member.roles):
                continue
            try:
                await member.add_roles(role, reason="Birthday")
            except discord.HTTPException:
                self.logger.warning(f"community: could not give the birthday role in guild {guild.id}", exc_info=True)
                given_all = False
                continue
            self.store.add_birthday_role(guild.id, member.id, role.id, midnight.timestamp())
        return given_all

    async def _remove_expired_birthday_roles(self) -> None:
        """Takes back birthday roles whose day is over; a failed removal is kept and retried."""
        for guild_id, user_id, role_id, given_by_bot in self.store.due_birthday_roles(self._now()):
            key = ("role", guild_id, user_id, role_id)
            if not self._may_retry(key):
                continue
            guild = self.bot.get_guild(guild_id)
            if guild is None or getattr(guild, "unavailable", False):
                continue  # not loaded yet (or an outage): the entry waits until the guild is back
            role = guild.get_role(role_id)
            member = guild.get_member(user_id)
            if member is None and role is not None and given_by_bot:
                # Not cached is not the same as gone (e.g. right after a restart): ask Discord.
                try:
                    member = await guild.fetch_member(user_id)
                except discord.NotFound:
                    member = None  # really left
                except discord.HTTPException:
                    self._failed(key)
                    continue
            # A member who left or a deleted role has nothing to take back.
            if member is not None and role is not None and given_by_bot:
                try:
                    await member.remove_roles(role, reason="Birthday is over")
                except discord.NotFound:
                    pass  # the member or role is gone
                except discord.HTTPException:
                    if self._failed(key) == 1:
                        self.logger.warning(
                            f"community: could not remove the birthday role in guild {guild_id}; will keep trying", exc_info=True
                        )
                    continue
            self._retries.pop(key, None)
            self.store.forget_birthday_role(guild_id, user_id, role_id)

    async def celebrate_anniversaries(self, guild: discord.Guild, settings: GuildSettings, local: datetime) -> bool:
        """Posts one message for every member who joined on this day in an earlier year; False when it could not be posted."""
        zone = local.tzinfo
        hidden = self.store.read_optouts(guild.id)  # hidden members are not named; unreadable: the job is retried
        found = [(m, anniversary_years(local.date(), m.joined_at, zone)) for m in guild.members if not m.bot and m.id not in hidden]
        found = [(m, years) for m, years in found if years > 0][: self.limits.birthday_max_mentions]
        if not found:
            return True
        channel = self._channel_for(guild, settings)
        if channel is None:
            return False  # tried again later, in case a channel is set
        members = [m for m, _ in found]
        mentions = [m.mention for m in members]
        facts = "Members: " + ", ".join(
            f"<<<{m.display_name}>>> (mention as {m.mention}), {years} year(s)" for m, years in found
        )
        text = await self._write(channel, _ANNIVERSARY_TASK, facts, mentions, self.limits.birthday_use_ai)
        if not text:
            lines = "\n".join(self._t(guild.id, "anniversary_line", mention=m.mention, years=years) for m, years in found)
            text = self._t(guild.id, "anniversary", lines=lines)
        return await self._send(channel, text, members)

    # ------------------------------------------------------------ weekly recap
    def title_name(self, guild_id: Any, title_id: str) -> str:
        return self._t(guild_id, f"title_{title_id}")

    async def post_weekly_recap(
        self, guild: discord.Guild, settings: GuildSettings, start: datetime, end: datetime, *, preview_channel: Any = None
    ) -> Optional[discord.Embed]:
        """Builds the recap of ``[start, end)`` and posts it (or, for a preview, only returns it).

        A quiet week (fewer than ``weekly_min_messages``) is skipped, except in a preview.
        Posting also hands this week's rotating titles to their new holders.

        Raises:
            discord.HTTPException: The recap could not be posted (so the scheduler retries it).
        """
        recap = await RecapBuilder(self.bot, self.limits).build(guild, start, end, self.store.read_optouts(guild.id))
        if recap is None:
            return None
        if preview_channel is None and recap.total < self.limits.weekly_min_messages:
            self.logger.info(f"community: skipping the weekly recap of guild {guild.id} ({recap.total} messages)")
            return None
        channel = preview_channel or self._channel_for(guild, settings, settings.weekly_channel_id)
        if channel is None:
            return None
        title_name = lambda title_id: self.title_name(guild.id, title_id)  # noqa: E731
        task = _WEEKLY_TASK.format(chars=self.limits.weekly_max_report_chars)
        report = await self._write(channel, task, recap_facts(recap, title_name), [], self.limits.weekly_use_ai)
        embed = format_recap(recap, lambda key, **kw: self._t(guild.id, key, **kw), title_name, guild.name, report)
        if preview_channel is None:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            self.store.set_titles(guild.id, recap.week, {title_id: member.id for title_id, (member, _) in recap.titles.items()})
        return embed

    async def _weekly_job(self, guild: discord.Guild, settings: GuildSettings, start: datetime, end: datetime) -> bool:
        """Posts the recap; False (tried again later) while there is no channel or no message stats."""
        if self._channel_for(guild, settings, settings.weekly_channel_id) is None:
            return False
        if getattr(self.bot, "stats_collector", None) is None:
            return False
        await self.post_weekly_recap(guild, settings, start, end)
        return True

    # ------------------------------------------------------------ admin commands
    async def _can_manage(self, interaction: discord.Interaction) -> bool:
        """Checks Manage Server (or bot owner) and answers the user when they lack it."""
        permissions = getattr(interaction.user, "guild_permissions", None)
        if (permissions is not None and permissions.manage_guild) or interaction.user.id == getattr(tokens, "bot_owner_id", 0):
            return True
        await interaction.response.send_message(self._t(interaction.guild_id, "no_permission"), ephemeral=True)
        return False

    def _status_text(self, guild: discord.Guild, settings: GuildSettings) -> str:
        def channel(channel_id: Optional[int]) -> str:
            return f"<#{channel_id}>" if channel_id else self._t(guild.id, "not_set")

        def on_off(value: bool) -> str:
            return self._t(guild.id, "on" if value else "off")

        zone = settings.timezone or self.limits.default_timezone or self._t(guild.id, "host_timezone")
        return self._t(
            guild.id,
            "status",
            announce=channel(settings.announce_channel_id),
            timezone=zone,
            welcome=on_off(settings.welcome_enabled),
            welcome_channel=channel(settings.welcome_channel_id),
            farewell=on_off(settings.farewell_enabled),
            birthday=on_off(settings.birthday_enabled),
            hour=settings.birthday_hour,
            role=f"<@&{settings.birthday_role_id}>" if settings.birthday_role_id else self._t(guild.id, "not_set"),
            anniversary=on_off(settings.anniversary_enabled),
            achievements=self._t(guild.id, f"achievement_mode_{settings.achievement_mode}"),
            weekly=on_off(settings.weekly_enabled),
            weekly_day=self._t(guild.id, f"weekday_{settings.weekly_day}"),
            weekly_hour=settings.weekly_hour,
            weekly_channel=channel(settings.weekly_channel_id),
            playing=on_off(settings.playing_enabled),
            playing_channel=channel(settings.playing_channel_id),
            playing_min=settings.playing_min_players,
        )

    @community.command(name="status", description="Show which community features are on")
    async def status(self, interaction: discord.Interaction) -> None:
        if not await self._can_manage(interaction):
            return
        settings = self.store.get_settings(interaction.guild_id)
        await interaction.response.send_message(self._status_text(interaction.guild, settings), ephemeral=True)

    @community.command(name="channel", description="Set the default channel for community announcements")
    @app_commands.describe(channel="Where welcomes, birthdays and anniversaries are posted")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        if not await self._can_manage(interaction):
            return
        self.store.update_settings(interaction.guild_id, announce_channel_id=channel.id)
        await interaction.response.send_message(self._t(interaction.guild_id, "channel_set", channel=channel.mention), ephemeral=True)

    @community.command(name="timezone", description="Set this server's time zone for daily messages")
    @app_commands.describe(name="An IANA time zone such as Asia/Taipei; leave empty to use the bot's default")
    async def set_timezone(self, interaction: discord.Interaction, name: Optional[str] = None) -> None:
        if not await self._can_manage(interaction):
            return
        name = (name or "").strip()
        if name and parse_timezone(name) is None:
            await interaction.response.send_message(self._t(interaction.guild_id, "invalid_timezone", name=name), ephemeral=True)
            return
        settings = self.store.update_settings(interaction.guild_id, timezone=name or None)
        now = self._local_now(settings)
        await interaction.response.send_message(
            self._t(interaction.guild_id, "timezone_set", name=name or "-", time=now.strftime("%Y-%m-%d %H:%M")),
            ephemeral=True,
        )

    @community.command(name="welcome", description="Welcome new members with a message written by the bot")
    @app_commands.describe(
        enabled="Turn welcomes on or off",
        channel="Where to post welcomes (defaults to the announcement channel)",
        note="Something every welcome should point out, such as the rules channel",
        farewell="Also post a short line when someone leaves",
    )
    async def welcome_command(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        channel: Optional[discord.TextChannel] = None,
        note: Optional[app_commands.Range[str, 0, 300]] = None,
        farewell: Optional[bool] = None,
    ) -> None:
        if not await self._can_manage(interaction):
            return
        changes: Dict[str, Any] = {"welcome_enabled": enabled}
        if channel is not None:
            changes["welcome_channel_id"] = channel.id
        if note is not None:
            changes["welcome_note"] = note.strip()
        if farewell is not None:
            changes["farewell_enabled"] = farewell
        settings = self.store.update_settings(interaction.guild_id, **changes)
        key = "welcome_on" if enabled else "welcome_off"
        text = self._t(interaction.guild_id, key)
        if enabled and self._channel_for(interaction.guild, settings, settings.welcome_channel_id) is None:
            text += "\n" + self._t(interaction.guild_id, "no_channel")
        await interaction.response.send_message(text, ephemeral=True)

    @community.command(name="welcome_test", description="Preview the welcome message with yourself as the new member")
    async def welcome_test(self, interaction: discord.Interaction) -> None:
        if not await self._can_manage(interaction):
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        text = await self.welcome(interaction.guild, [interaction.user], preview_channel=interaction.channel)
        await interaction.followup.send(text or self._t(interaction.guild_id, "no_channel"), ephemeral=True)

    @community.command(name="birthdays", description="Celebrate members' birthdays on this server")
    @app_commands.describe(
        enabled="Turn birthday messages on or off",
        hour="Local hour (0-23) to post birthday and anniversary messages",
        role="A role given to birthday members for the day",
    )
    async def birthdays_command(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        hour: Optional[app_commands.Range[int, 0, 23]] = None,
        role: Optional[discord.Role] = None,
    ) -> None:
        if not await self._can_manage(interaction):
            return
        changes: Dict[str, Any] = {"birthday_enabled": enabled}
        if hour is not None:
            changes["birthday_hour"] = hour
        if role is not None:
            problem = self._birthday_role_problem(interaction, role)
            if problem:
                await interaction.response.send_message(self._t(interaction.guild_id, problem, role=role.mention), ephemeral=True)
                return
            changes["birthday_role_id"] = role.id
        settings = self.store.update_settings(interaction.guild_id, **changes)
        key = "birthday_on" if enabled else "birthday_off"
        await interaction.response.send_message(self._t(interaction.guild_id, key, hour=settings.birthday_hour), ephemeral=True)

    @classmethod
    def _birthday_role_problem(cls, interaction: discord.Interaction, role: discord.Role) -> Optional[str]:
        """Why ``role`` cannot be the birthday role, as a response key; None when it can.

        The bot hands the role out by itself, so the admin must be able to give it themselves
        (Manage Roles and a higher top role, or the server owner), on top of ``_unsafe_birthday_role``.
        """
        guild, user = interaction.guild, interaction.user
        problem = cls._unsafe_birthday_role(guild, role)
        if problem:
            return problem
        if user.id != guild.owner_id:
            permissions = getattr(user, "guild_permissions", None)
            top_role = getattr(user, "top_role", None)
            if permissions is None or not permissions.manage_roles or top_role is None or role >= top_role:
                return "birthday_role_not_yours"
        return None

    @staticmethod
    def _unsafe_birthday_role(guild: discord.Guild, role: discord.Role) -> Optional[str]:
        """Why the bot must not hand ``role`` out, as a response key; None when it may.

        The bot must be able to manage the role (Manage Roles and a higher role), and the role
        must not carry moderator permissions, voice moderation included.
        """
        me = getattr(guild, "me", None)
        if me is None or not me.guild_permissions.manage_roles:
            return "birthday_role_bot_cannot"
        if not role.is_assignable():
            return "birthday_role_unassignable"
        if role.permissions.value & _UNSAFE_ROLE_PERMISSIONS.value:
            return "birthday_role_elevated"
        return None

    @community.command(name="anniversaries", description="Celebrate the yearly anniversary of when members joined")
    @app_commands.describe(enabled="Turn anniversary messages on or off")
    async def anniversaries_command(self, interaction: discord.Interaction, enabled: bool) -> None:
        if not await self._can_manage(interaction):
            return
        settings = self.store.update_settings(interaction.guild_id, anniversary_enabled=enabled)
        key = "anniversary_on" if enabled else "anniversary_off"
        await interaction.response.send_message(self._t(interaction.guild_id, key, hour=settings.birthday_hour), ephemeral=True)

    @community.command(name="achievements", description="Choose how unlocked achievements are announced")
    @app_commands.describe(mode="Off keeps them in /profile and /achievements only")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Off", value="off"),
            app_commands.Choice(name="Reply to the message", value="reply"),
            app_commands.Choice(name="Announcement channel", value="channel"),
        ]
    )
    async def achievements_command(self, interaction: discord.Interaction, mode: str) -> None:
        if not await self._can_manage(interaction):
            return
        settings = self.store.update_settings(interaction.guild_id, achievement_mode=mode)
        text = self._t(interaction.guild_id, f"achievements_{mode}")
        if mode == "channel" and self._channel_for(interaction.guild, settings) is None:
            text += "\n" + self._t(interaction.guild_id, "no_channel")
        await interaction.response.send_message(text, ephemeral=True)

    @community.command(name="weekly", description="Post a weekly recap of the server's week")
    @app_commands.describe(
        enabled="Turn the weekly recap on or off",
        channel="Where to post it (defaults to the announcement channel)",
        day="Local weekday to post it (default Sunday)",
        hour="Local hour (0-23) to post it (default 20)",
    )
    @app_commands.choices(day=_WEEKDAYS)
    async def weekly_command(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        channel: Optional[discord.TextChannel] = None,
        day: Optional[int] = None,
        hour: Optional[app_commands.Range[int, 0, 23]] = None,
    ) -> None:
        if not await self._can_manage(interaction):
            return
        changes: Dict[str, Any] = {"weekly_enabled": enabled}
        if channel is not None:
            changes["weekly_channel_id"] = channel.id
        if day is not None:
            changes["weekly_day"] = day
        if hour is not None:
            changes["weekly_hour"] = hour
        settings = self.store.update_settings(interaction.guild_id, **changes)
        if not enabled:
            await interaction.response.send_message(self._t(interaction.guild_id, "weekly_off"), ephemeral=True)
            return
        text = self._t(
            interaction.guild_id,
            "weekly_on",
            day=self._t(interaction.guild_id, f"weekday_{settings.weekly_day}"),
            hour=settings.weekly_hour,
            count=self.limits.weekly_min_messages,
        )
        if self._channel_for(interaction.guild, settings, settings.weekly_channel_id) is None:
            text += "\n" + self._t(interaction.guild_id, "no_channel")
        await interaction.response.send_message(text, ephemeral=True)

    @community.command(name="playing", description="Point out when several members play the same game")
    @app_commands.describe(
        enabled="Turn it on or off",
        channel="Where to post (defaults to the announcement channel)",
        min_players="How many members must play the same game (default 3)",
    )
    async def playing_command(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        channel: Optional[discord.TextChannel] = None,
        min_players: Optional[app_commands.Range[int, 2, 25]] = None,
    ) -> None:
        if not await self._can_manage(interaction):
            return
        changes: Dict[str, Any] = {"playing_enabled": enabled}
        if channel is not None:
            changes["playing_channel_id"] = channel.id
        if min_players is not None:
            changes["playing_min_players"] = min_players
        settings = self.store.update_settings(interaction.guild_id, **changes)
        if enabled:
            text = self._t(interaction.guild_id, "playing_on", count=settings.playing_min_players)
            target = self._channel_for(interaction.guild, settings, settings.playing_channel_id)
            if target is None:
                text += "\n" + self._t(interaction.guild_id, "no_channel")
        else:
            text = self._t(interaction.guild_id, "playing_off")
        await interaction.response.send_message(text, ephemeral=True)

    @community.command(name="weekly_preview", description="Preview this week's recap so far (only you see it)")
    async def weekly_preview(self, interaction: discord.Interaction) -> None:
        if not await self._can_manage(interaction):
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        settings = self.store.get_settings(interaction.guild_id)
        local = self._local_now(settings)
        monday = local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=local.weekday())
        embed = await self.post_weekly_recap(interaction.guild, settings, monday, local, preview_channel=interaction.channel)
        if embed is None:
            await interaction.followup.send(self._t(interaction.guild_id, "weekly_unavailable"), ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------ member commands
    @birthday.command(name="set", description="Save your birthday on this server (no year needed)")
    @app_commands.describe(month="Month (1-12)", day="Day of the month")
    async def birthday_set(
        self, interaction: discord.Interaction, month: app_commands.Range[int, 1, 12], day: app_commands.Range[int, 1, 31]
    ) -> None:
        if not is_valid_birthday(month, day):
            await interaction.response.send_message(self._t(interaction.guild_id, "invalid_date"), ephemeral=True)
            return
        self.store.set_birthday(interaction.guild_id, interaction.user.id, month, day)
        text = self._t(interaction.guild_id, "birthday_saved", month=month, day=day)
        if not self.store.get_settings(interaction.guild_id).birthday_enabled:
            text += "\n" + self._t(interaction.guild_id, "birthday_feature_off")
        await interaction.response.send_message(text, ephemeral=True)

    @birthday.command(name="remove", description="Remove your saved birthday from this server")
    async def birthday_remove(self, interaction: discord.Interaction) -> None:
        removed = self.store.remove_birthday(interaction.guild_id, interaction.user.id)
        key = "birthday_removed" if removed else "birthday_none"
        await interaction.response.send_message(self._t(interaction.guild_id, key), ephemeral=True)

    @birthday.command(name="upcoming", description="Show birthdays in the next 30 days on this server")
    async def birthday_upcoming(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        settings = self.store.get_settings(guild.id)
        today = self._local_now(settings).date()
        # Members hidden with /leaderboard optout are left out, except the one asking (the reply is ephemeral).
        hidden = self.store.optouts(guild.id) - {interaction.user.id}
        rows = [
            (guild.get_member(user_id), when)
            for user_id, when in upcoming_birthdays(today, self.store.birthdays(guild.id), self.UPCOMING_DAYS)
            if user_id not in hidden
        ]
        lines = [
            self._t(guild.id, "upcoming_line", date=f"{when.month}/{when.day}", name=member.display_name)
            for member, when in rows
            if member is not None
        ]
        text = self._t(guild.id, "upcoming_title") + "\n" + "\n".join(lines) if lines else self._t(guild.id, "upcoming_none")
        await interaction.response.send_message(text, ephemeral=True)


def split_message(text: str, limit: int = MESSAGE_LIMIT) -> List[str]:
    """Splits ``text`` into messages of at most ``limit`` characters, at line breaks or spaces when possible."""
    chunks: List[str] = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit + 1)
        if cut <= 0:
            cut = text.rfind(" ", 0, limit + 1)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n ")
    if text:
        chunks.append(text)
    return chunks


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommunityCog(bot))
