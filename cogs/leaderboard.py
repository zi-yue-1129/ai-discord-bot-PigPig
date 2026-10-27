"""Leaderboards, member profiles and achievements.

Everyone is on the leaderboards by default; a member can hide themselves with
``/leaderboard optout``, which also keeps them out of achievement announcements. Achievements
are unlocked from the stats StatsCog keeps (it dispatches ``user_stats_updated`` after each
message) and are announced only when a server admin picks a mode with
``/community achievements``.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from addons.settings import base_config
from function import func
from llm.tools.user_stats import _format_text_card, _make_t, fetch_public_terms, public_view

from .community import COMMUNITY_DB_PATH
from .community_lib.achievements import (
    DEFAULT_ACHIEVEMENTS,
    Achievement,
    load_achievements,
    reached,
    stat_values,
)
from .community_lib.dates import local_now
from .community_lib.limits import CommunityLimits
from .community_lib.recap import TITLES
from .community_lib.store import CommunityStore
from .language_manager import LanguageManager

_BUILT_IN_IDS = {achievement.id for achievement in DEFAULT_ACHIEVEMENTS}
# Achievements earned by the message itself (ending a long silence) are announced even the
# first time a member is checked; progress made before achievements existed is recorded quietly.
_EVENT_STATS = {"gap_days"}
_MEDALS = ["🥇", "🥈", "🥉"]


class LeaderboardCog(commands.Cog):
    """Ranks members, shows profiles and hands out achievements."""

    TOP = 10

    leaderboard = app_commands.Group(name="leaderboard", description="Server rankings", guild_only=True)

    def __init__(self, bot: commands.Bot, store: Optional[CommunityStore] = None) -> None:
        self.bot = bot
        self.store = store or CommunityStore(COMMUNITY_DB_PATH)
        community = getattr(base_config, "community", {}) or {}
        self.limits = CommunityLimits.from_config(community)
        self.achievements: List[Achievement] = load_achievements(community.get("achievements"))
        self._by_id = {achievement.id: achievement for achievement in self.achievements}
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="leaderboard")
        self._now = time.time
        self._unlocked: Dict[Tuple[int, int], Set[str]] = {}
        self._announced: Dict[Tuple[int, int], str] = {}

    async def cog_load(self) -> None:
        self.lang_manager = LanguageManager.get_instance(self.bot)

    # ------------------------------------------------------------ helpers
    def _t(self, guild_id: Any, *keys: str, **kwargs: Any) -> str:
        if self.lang_manager is None:
            return keys[-1]
        return self.lang_manager.translate(str(guild_id), "commands", "leaderboard", *keys, **kwargs)

    def _r(self, guild_id: Any, key: str, **kwargs: Any) -> str:
        return self._t(guild_id, "responses", key, **kwargs)

    def _stats_storage(self) -> Any:
        cog = self.bot.get_cog("StatsCog") if hasattr(self.bot, "get_cog") else None
        return getattr(cog, "stats_storage", None)

    def _local_now(self, guild_id: int) -> datetime:
        settings = self.store.get_settings(guild_id)
        return local_now(datetime.fromtimestamp(self._now(), timezone.utc), settings.timezone, self.limits.default_timezone)

    def achievement_name(self, guild_id: int, achievement: Achievement) -> str:
        if achievement.name:
            return achievement.name
        if achievement.id in _BUILT_IN_IDS:
            return self._t(guild_id, "achievements", achievement.id)
        return achievement.id

    def achievement_description(self, guild_id: int, achievement: Achievement) -> str:
        if achievement.description:
            return achievement.description
        parts = []
        for stat, minimum in achievement.when.items():
            value = f"{minimum:.0%}" if stat == "night_ratio" else f"{minimum:,.0f}"
            parts.append(self._r(guild_id, f"needs_{stat}", value=value))
        return self._r(guild_id, "needs_joiner").join(parts)

    def _title(self, guild_id: int, title_id: str) -> str:
        """A rotating title (from the weekly recap) with its emoji."""
        emoji = dict(TITLES).get(title_id, "🏷️")
        if self.lang_manager is None:
            return f"{emoji} {title_id}"
        return f"{emoji} " + self.lang_manager.translate(str(guild_id), "commands", "community", "responses", f"title_{title_id}")

    def _label(self, guild_id: int, achievement: Achievement) -> str:
        return f"{achievement.emoji} **{self.achievement_name(guild_id, achievement)}**"

    def _ranked_members(self, guild: discord.Guild, rows: Sequence[Tuple[Any, int]]) -> List[Tuple[Any, int]]:
        """Keeps rows of current, human, not opted-out members, as ``(member, value)``."""
        hidden = self.store.optouts(guild.id)
        ranked = []
        for user_id, value in rows:
            try:
                member_id = int(user_id)
            except (TypeError, ValueError):
                continue
            member = guild.get_member(member_id)
            if member is None or member.bot or member_id in hidden:
                continue
            ranked.append((member, int(value)))
        return ranked

    async def rankings(self, guild: discord.Guild, kind: str, period: str) -> Optional[List[Tuple[Any, int]]]:
        """Returns ``(member, value)`` pairs, best first; None when the needed stats are unavailable."""
        if kind == "streak":
            storage = self._stats_storage()
            rows = await storage.get_guild_rankings(str(guild.id), "streak") if storage else None
        elif kind == "games":
            rows = self.store.game_points(guild.id, self._period_start(guild.id, period))
        elif period == "all":
            storage = self._stats_storage()
            rows = await storage.get_guild_rankings(str(guild.id), "total") if storage else None
        else:
            collector = getattr(self.bot, "stats_collector", None)
            if collector is None:
                return None
            rows = await collector.message_counts_by_user(str(guild.id), self._period_start(guild.id, period), self._now() + 1)
        return None if rows is None else self._ranked_members(guild, rows)

    def _period_start(self, guild_id: int, period: str) -> float:
        """UNIX time the period began: local Monday 00:00, the 1st of the month, or 0 for all time."""
        if period == "all":
            return 0.0
        local = self._local_now(guild_id)
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
        start = start - timedelta(days=start.weekday()) if period == "week" else start.replace(day=1)
        return start.timestamp()

    # ------------------------------------------------------------ achievements
    @commands.Cog.listener()
    async def on_user_stats_updated(self, message: discord.Message, stats: Dict[str, Any]) -> None:
        if message.guild is None or message.author.bot:
            return
        try:
            await self.check_achievements(message, stats)
        except Exception as error:
            self.logger.error("leaderboard: checking achievements failed", exc_info=True)
            await func.report_error(error, "leaderboard: checking achievements")

    async def check_achievements(self, message: discord.Message, stats: Dict[str, Any]) -> List[str]:
        """Unlocks what the member has reached and announces it; returns the newly unlocked IDs."""
        guild, member = message.guild, message.author
        key = (guild.id, member.id)
        known = self._unlocked.get(key)
        first_check = False
        if known is None:
            known = {achievement_id for achievement_id, _ in self.store.achievements(*key)}
            self._unlocked[key] = known
            first_check = not self.store.was_checked(*key)
            if first_check:
                self.store.mark_checked(*key)

        values = stat_values(stats, datetime.fromtimestamp(self._now(), timezone.utc))
        candidates = [achievement_id for achievement_id in reached(self.achievements, values) if achievement_id not in known]
        if not candidates:
            return []
        new = self.store.unlock(guild.id, member.id, candidates, self._now())
        known.update(new)
        if first_check:
            new_to_announce = [i for i in new if _EVENT_STATS & set(self._by_id[i].when)]
        else:
            new_to_announce = new
        if new_to_announce:
            await self._announce(message, [self._by_id[i] for i in new_to_announce])
        return new

    async def _announce(self, message: discord.Message, unlocked: List[Achievement]) -> None:
        guild, member = message.guild, message.author
        settings = self.store.get_settings(guild.id)
        if settings.achievement_mode not in ("reply", "channel") or self.store.is_opted_out(guild.id, member.id):
            return
        key = (guild.id, member.id)
        today = self._local_now(guild.id).date().isoformat()
        if self._announced.get(key) == today:
            return  # at most one announcement per member per day
        self._announced[key] = today

        labels = self._r(guild.id, "list_joiner").join(self._label(guild.id, a) for a in unlocked)
        text = self._r(guild.id, "unlocked", name=member.mention, achievements=labels)
        quiet = discord.AllowedMentions.none()
        try:
            if settings.achievement_mode == "reply":
                await message.add_reaction("🏆")
                await message.reply(text, mention_author=False, allowed_mentions=quiet)
            else:
                channel = guild.get_channel(settings.announce_channel_id) if settings.announce_channel_id else None
                channel = channel or guild.system_channel
                if channel is not None:
                    await channel.send(text, allowed_mentions=quiet)
        except discord.HTTPException:
            self.logger.warning(f"leaderboard: could not announce an achievement in guild {guild.id}", exc_info=True)

    # ------------------------------------------------------------ commands
    @leaderboard.command(name="top", description="Show who talks the most on this server")
    @app_commands.describe(period="Which messages to count", kind="Rank by messages, daily streak or game points")
    @app_commands.choices(
        period=[
            app_commands.Choice(name="This week", value="week"),
            app_commands.Choice(name="This month", value="month"),
            app_commands.Choice(name="All time", value="all"),
        ],
        kind=[
            app_commands.Choice(name="Messages", value="messages"),
            app_commands.Choice(name="Daily streak", value="streak"),
            app_commands.Choice(name="Game points", value="games"),
        ],
    )
    async def top(self, interaction: discord.Interaction, period: str = "week", kind: str = "messages") -> None:
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        ranked = await self.rankings(guild, kind, period)
        if ranked is None:
            await interaction.followup.send(self._r(guild.id, "unavailable"))
            return
        await interaction.followup.send(
            self.leaderboard_text(guild.id, ranked, kind, period, interaction.user.id),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    def leaderboard_text(self, guild_id: int, ranked: List[Tuple[Any, int]], kind: str, period: str, viewer_id: int) -> str:
        if kind == "streak":
            title, unit = self._r(guild_id, "title_streak"), "value_streak"
        elif kind == "games":
            title, unit = self._r(guild_id, f"title_games_{period}"), "value_points"
        else:
            title, unit = self._r(guild_id, f"title_{period}"), "value_messages"
        if not ranked:
            return title + "\n" + self._r(guild_id, "empty")
        lines = [title]
        for place, (member, value) in enumerate(ranked[: self.TOP], start=1):
            badge = _MEDALS[place - 1] if place <= len(_MEDALS) else f"`#{place}`"
            lines.append(f"{badge} **{member.display_name}** — {self._r(guild_id, unit, count=f'{value:,}')}")
        if self.store.is_opted_out(guild_id, viewer_id):
            lines.append(self._r(guild_id, "you_hidden"))
        else:
            mine = next(((place, value) for place, (m, value) in enumerate(ranked, start=1) if m.id == viewer_id), None)
            if mine is None:
                lines.append(self._r(guild_id, "you_unranked"))
            elif mine[0] > self.TOP:
                lines.append(self._r(guild_id, "your_rank", rank=mine[0], value=self._r(guild_id, unit, count=f"{mine[1]:,}")))
        return "\n".join(lines)

    @leaderboard.command(name="optout", description="Hide yourself from rankings, recaps and achievement announcements")
    @app_commands.describe(hide="True to hide yourself, False to show up again")
    async def optout(self, interaction: discord.Interaction, hide: bool) -> None:
        self.store.set_optout(interaction.guild_id, interaction.user.id, hide)
        await interaction.response.send_message(self._r(interaction.guild_id, "hidden" if hide else "shown"), ephemeral=True)

    async def _visible_target(self, interaction: discord.Interaction, user: Optional[discord.Member]) -> Optional[Any]:
        """Returns the member to show, or None after telling the viewer they cannot see them."""
        target = user or interaction.user
        if target.id != interaction.user.id and self.store.is_opted_out(interaction.guild_id, target.id):
            await interaction.response.send_message(
                self._r(interaction.guild_id, "profile_hidden", name=target.display_name), ephemeral=True
            )
            return None
        return target

    def _private(self, interaction: discord.Interaction, target: Any) -> bool:
        """Whether to answer only the viewer: a hidden member looking at themselves stays hidden."""
        return self.store.is_opted_out(interaction.guild_id, target.id)

    @app_commands.command(name="profile", description="Show a member's activity card and badges on this server")
    @app_commands.describe(user="Whose profile to show (defaults to you)")
    @app_commands.guild_only()
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None) -> None:
        target = await self._visible_target(interaction, user)
        if target is None:
            return
        await interaction.response.send_message(
            await self.profile_text(interaction.guild, target),
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=self._private(interaction, target),
        )

    async def profile_text(self, guild: discord.Guild, member: Any) -> str:
        storage = self._stats_storage()
        stats = await storage.get_user_stats(str(member.id), str(guild.id)) if storage else None
        if not stats:
            return self._r(guild.id, "no_stats", name=member.display_name)
        terms = await fetch_public_terms(storage, guild, str(member.id))
        extras = await self.profile_extras(guild, member)
        # Built after the last await, so a channel made private meanwhile is left out.
        shown = public_view(guild, stats, terms)
        lines = [_format_text_card(member.display_name, shown, _make_t(self.bot, str(guild.id)))]
        return "\n".join(lines + extras)

    async def profile_extras(self, guild: discord.Guild, member: Any, titles: bool = True) -> List[str]:
        """The profile lines after the stats card: all-time rank (unless hidden), titles and badges.

        Args:
            titles: Include the rotating titles. The weekly recap awards them from activity in
                every channel (and from the music log), so answers posted for everyone leave them out.
        """
        lines = []
        if not self.store.is_opted_out(guild.id, member.id):
            ranked = await self.rankings(guild, "messages", "all") or []
            place = next((place for place, (m, _) in enumerate(ranked, start=1) if m.id == member.id), None)
            if place is not None:
                lines.append(self._r(guild.id, "profile_rank", rank=place, total=len(ranked)))
        held = self.store.titles_of(guild.id, member.id) if titles else []
        if held:
            names = self._r(guild.id, "list_joiner").join(self._title(guild.id, title_id) for title_id in held)
            lines.append(self._r(guild.id, "profile_titles", titles=names))
        unlocked = [self._by_id[i] for i, _ in self.store.achievements(guild.id, member.id) if i in self._by_id]
        if unlocked:
            badges = " ".join(a.emoji for a in unlocked)
            lines.append(self._r(guild.id, "profile_badges", badges=badges, done=len(unlocked), total=len(self.achievements)))
        return lines

    @app_commands.command(name="achievements", description="Show which achievements a member has unlocked")
    @app_commands.describe(user="Whose achievements to show (defaults to you)")
    @app_commands.guild_only()
    async def achievements_command(self, interaction: discord.Interaction, user: Optional[discord.Member] = None) -> None:
        target = await self._visible_target(interaction, user)
        if target is None:
            return
        await interaction.response.send_message(
            self.achievements_text(interaction.guild_id, target),
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=self._private(interaction, target),
        )

    def achievements_text(self, guild_id: int, member: Any) -> str:
        unlocked = dict(self.store.achievements(guild_id, member.id))
        done = sum(1 for a in self.achievements if a.id in unlocked)
        lines = [self._r(guild_id, "achievements_title", name=member.display_name, done=done, total=len(self.achievements))]
        for achievement in self.achievements:
            description = self.achievement_description(guild_id, achievement)
            if achievement.id in unlocked:
                when = datetime.fromtimestamp(unlocked[achievement.id], timezone.utc).strftime("%Y-%m-%d")
                lines.append(f"✅ {self._label(guild_id, achievement)} — {description} ({when})")
            else:
                lines.append(f"🔒 {self._label(guild_id, achievement)} — {description}")
        return "\n".join(lines)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
