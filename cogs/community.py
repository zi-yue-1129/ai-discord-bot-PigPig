"""Community features: welcoming new members, birthdays, yearly join anniversaries and achievement announcements.

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
from typing import Any, Dict, List, Optional, Sequence

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
from .community_lib.store import CommunityStore, GuildSettings
from .language_manager import LanguageManager

COMMUNITY_DB_PATH = "data/community.db"

_WELCOME_TASK = (
    "New members just joined this Discord server. Welcome them warmly and briefly (one to three "
    "sentences), mention each of them, and weave in the admin's note if there is one."
)
_BIRTHDAY_TASK = "Today is the birthday of the members below. Wish them a happy birthday, mentioning each of them."
_ANNIVERSARY_TASK = (
    "Today is the yearly anniversary of the day the members below joined this server. Congratulate "
    "them and say how many years each has been here, mentioning each of them."
)


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
        """Posts ``text``, allowing pings only for ``members``."""
        allowed = discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(id=m.id) for m in members])
        try:
            await channel.send(text, allowed_mentions=allowed)
            return True
        except discord.HTTPException:
            self.logger.warning(f"community: could not post in channel {getattr(channel, 'id', None)}", exc_info=True)
            return False

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
            self._flushes.pop(guild.id, None)

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
        """Posts today's birthday and anniversary messages that are due, and takes back expired birthday roles."""
        await self._remove_expired_birthday_roles()
        for settings in self.store.guilds_with_daily_jobs():
            guild = self.bot.get_guild(settings.guild_id)
            if guild is None:
                continue
            local = self._local_now(settings)
            if local.hour < settings.birthday_hour:
                continue
            today = local.date().isoformat()
            if settings.birthday_enabled and self.store.claim_run(guild.id, "birthday", today):
                await self.celebrate_birthdays(guild, settings, local)
            if settings.anniversary_enabled and self.store.claim_run(guild.id, "anniversary", today):
                await self.celebrate_anniversaries(guild, settings, local)

    async def celebrate_birthdays(self, guild: discord.Guild, settings: GuildSettings, local: datetime) -> None:
        """Posts one message for everyone whose birthday is today and gives the birthday role."""
        ids = birthdays_on(local.date(), self.store.birthdays(guild.id))
        members = [m for m in (guild.get_member(user_id) for user_id in ids) if m is not None and not m.bot]
        members = members[: self.limits.birthday_max_mentions]
        if not members:
            return
        channel = self._channel_for(guild, settings)
        if channel is not None:
            mentions = [m.mention for m in members]
            facts = "Birthday members: " + ", ".join(f"<<<{m.display_name}>>> (mention as {m.mention})" for m in members)
            text = await self._write(channel, _BIRTHDAY_TASK, facts, mentions, self.limits.birthday_use_ai)
            await self._send(channel, text or self._t(guild.id, "birthday", mentions=" ".join(mentions)), members)
        if settings.birthday_role_id:
            await self._give_birthday_role(guild, settings.birthday_role_id, members, local)

    async def _give_birthday_role(
        self, guild: discord.Guild, role_id: int, members: Sequence[discord.Member], local: datetime
    ) -> None:
        role = guild.get_role(role_id)
        if role is None:
            return
        midnight = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        for member in members:
            try:
                await member.add_roles(role, reason="Birthday")
            except discord.HTTPException:
                self.logger.warning(f"community: could not give the birthday role in guild {guild.id}", exc_info=True)
                continue
            self.store.add_birthday_role(guild.id, member.id, role.id, midnight.timestamp())

    async def _remove_expired_birthday_roles(self) -> None:
        for guild_id, user_id, role_id in self.store.due_birthday_roles(self._now()):
            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(user_id) if guild is not None else None
            role = guild.get_role(role_id) if guild is not None else None
            if member is not None and role is not None:
                try:
                    await member.remove_roles(role, reason="Birthday is over")
                except discord.HTTPException:
                    self.logger.warning(f"community: could not remove the birthday role in guild {guild_id}", exc_info=True)
            self.store.forget_birthday_role(guild_id, user_id, role_id)

    async def celebrate_anniversaries(self, guild: discord.Guild, settings: GuildSettings, local: datetime) -> None:
        """Posts one message for every member who joined on this day in an earlier year."""
        zone = local.tzinfo
        found = [(m, anniversary_years(local.date(), m.joined_at, zone)) for m in guild.members if not m.bot]
        found = [(m, years) for m, years in found if years > 0][: self.limits.birthday_max_mentions]
        if not found:
            return
        channel = self._channel_for(guild, settings)
        if channel is None:
            return
        members = [m for m, _ in found]
        mentions = [m.mention for m in members]
        facts = "Members: " + ", ".join(
            f"<<<{m.display_name}>>> (mention as {m.mention}), {years} year(s)" for m, years in found
        )
        text = await self._write(channel, _ANNIVERSARY_TASK, facts, mentions, self.limits.birthday_use_ai)
        if not text:
            lines = "\n".join(self._t(guild.id, "anniversary_line", mention=m.mention, years=years) for m, years in found)
            text = self._t(guild.id, "anniversary", lines=lines)
        await self._send(channel, text, members)

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
            changes["birthday_role_id"] = role.id
        settings = self.store.update_settings(interaction.guild_id, **changes)
        key = "birthday_on" if enabled else "birthday_off"
        await interaction.response.send_message(self._t(interaction.guild_id, key, hour=settings.birthday_hour), ephemeral=True)

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
        rows = [
            (guild.get_member(user_id), when)
            for user_id, when in upcoming_birthdays(today, self.store.birthdays(guild.id), self.UPCOMING_DAYS)
        ]
        lines = [
            self._t(guild.id, "upcoming_line", date=f"{when.month}/{when.day}", name=member.display_name)
            for member, when in rows
            if member is not None
        ]
        text = self._t(guild.id, "upcoming_title") + "\n" + "\n".join(lines) if lines else self._t(guild.id, "upcoming_none")
        await interaction.response.send_message(text, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommunityCog(bot))
