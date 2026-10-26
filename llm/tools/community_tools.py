"""Community tools for LLM integration: rankings, achievements, the weekly recap and birthdays.

Every answer the model writes is posted in the channel for everyone there to read, so these
tools only return what the matching public post would show: members who hid themselves with
``/leaderboard optout`` are never named, and anything said in a channel is only used when every
member can read that channel. Names and other text members wrote are wrapped in ``<<< >>>`` so
the model treats them as data.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from langchain_core.tools.structured import StructuredTool

from addons.logging import get_logger
from llm.tools.user_stats import _is_hidden

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_logger = get_logger(server_id="Bot", source="llm.tools.community_tools")

# How long a built recap is reused: building one reads several tables and fetches messages.
RECAP_CACHE_SECONDS = 600
MAX_BIRTHDAYS = 15
# guild id, period -> (built at, local start, public channel ids then, recap)
_recap_cache: Dict[Tuple[int, str], Tuple[float, datetime, frozenset, Any]] = {}


def _resolve_member(guild: Any, user_id: Optional[str], author: Any) -> Tuple[Optional[Any], Optional[str]]:
    """The member ``user_id`` names (the author when empty), or None and the reason to give."""
    if not user_id:
        return author, None
    text = str(user_id).strip().strip("<@!>")
    if not text.isdigit():
        return None, f"{user_id!r} is not a Discord user ID; ask for the member's numeric ID or mention."
    member = guild.get_member(int(text))
    if member is None:
        return None, "That member is not on this server."
    return member, None


def _quote_channel(guild: Any, url: str) -> Any:
    """The channel of a message link (``.../channels/guild/channel/message``)."""
    parts = str(url or "").rstrip("/").split("/")
    if len(parts) < 3 or not parts[-2].isdigit():
        return None
    lookup = getattr(guild, "get_channel_or_thread", None) or guild.get_channel
    return lookup(int(parts[-2]))


def _still_shown(guild: Any, recap: Any, hidden: set) -> Any:
    """A copy of ``recap`` without what may no longer be shown: hidden members and channels that stopped being public."""
    from copy import copy

    from cogs.community_lib.recap import is_public

    def visible(member: Any) -> bool:
        return member is not None and member.id not in hidden and guild.get_member(member.id) is not None

    shown = copy(recap)
    shown.channels = [(c, n) for c, n in recap.channels if is_public(guild, c)]
    shown.talkers = [(m, n) for m, n in recap.talkers if visible(m)]
    shown.titles = {key: (m, n) for key, (m, n) in recap.titles.items() if visible(m)}
    shown.missing = [(m, d) for m, d in recap.missing if visible(m)]
    quote = recap.quote
    if quote and not (visible(quote["member"]) and is_public(guild, _quote_channel(guild, quote["url"]))):
        quote = None
    shown.quote = quote
    return shown


class CommunityTools:
    """Tools over the leaderboard and community cogs."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        self.runtime = runtime

    def _cog(self, name: str) -> Any:
        bot = getattr(self.runtime, "bot", None)
        return bot.get_cog(name) if bot is not None and hasattr(bot, "get_cog") else None

    def get_tools(self) -> list:
        runtime = self.runtime
        message = getattr(runtime, "message", None)
        guild = getattr(message, "guild", None)
        leaderboard = self._cog("LeaderboardCog")
        community = self._cog("CommunityCog")
        if guild is None:
            return []

        def hidden_here(user_id: Any) -> bool:
            return _is_hidden(runtime, guild.id, str(user_id))

        async def get_leaderboard(kind: str = "messages", period: str = "week") -> str:
            """Shows this server's leaderboard (top 10), the same as /leaderboard top.

            Call this when someone asks who talks the most, who has the longest daily streak or
            who has the most game points, or where they rank.

            Args:
                kind: "messages", "streak" (consecutive active days) or "games" (game points).
                period: "week", "month" or "all" (all time). Ignored for "streak".

            Returns:
                The ranking with display names, and the asker's own place when they are ranked.
            """
            kind = kind if kind in ("messages", "streak", "games") else "messages"
            period = period if period in ("week", "month", "all") else "week"
            ranked = await leaderboard.rankings(guild, kind, period)
            if ranked is None:
                return "The leaderboard is not available right now."
            # Members may have hidden themselves while the ranking was read.
            hidden = leaderboard.store.optouts(guild.id)
            ranked = [(m, v) for m, v in ranked if m.id not in hidden]
            return leaderboard.leaderboard_text(guild.id, ranked, kind, period, message.author.id)

        async def get_achievements(user_id: Optional[str] = None) -> str:
            """Lists a member's achievements: unlocked ones with their date, locked ones with what they need.

            Call this when someone asks which achievements or badges a member has, or how to
            unlock one.

            Args:
                user_id: Optional Discord user ID or mention. Defaults to the person asking.

            Returns:
                One line per achievement.
            """
            member, problem = _resolve_member(guild, user_id, message.author)
            if problem:
                return problem
            if hidden_here(member.id):
                if member.id == message.author.id:
                    return (
                        "This user hid themselves with /leaderboard optout, so their achievements are not shown in "
                        "chat. Tell them they can still see them privately with /achievements."
                    )
                return "This member chose to hide their stats (/leaderboard optout). Do not share or guess them."
            return leaderboard.achievements_text(guild.id, member)

        async def get_server_recap(period: str = "this_week") -> str:
            """Summarises the server's week: message count, busiest public channels, top talkers,
            hot words, quote and song of the week, the rotating titles and regulars who went quiet.

            Call this when someone asks how the server's week went, what was popular, or who holds
            a title such as the week's top talker.

            Args:
                period: "this_week" (so far) or "last_week".

            Returns:
                The facts, one per line; text members wrote is wrapped in <<< >>>.
            """
            from cogs.community_lib.recap import RecapBuilder, public_channel_ids, recap_facts

            period = period if period in ("this_week", "last_week") else "this_week"
            settings = community.store.get_settings(guild.id)
            local = community._local_now(settings)
            monday = local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=local.weekday())
            start, end = (monday, local) if period == "this_week" else (monday - timedelta(days=7), monday)
            key = (guild.id, period)
            cached = _recap_cache.get(key)
            # Words and emojis are counted per channel only while building, so a recap is rebuilt
            # as soon as the set of public channels changes.
            public = frozenset(public_channel_ids(guild))
            if cached and cached[1] == start and cached[2] == public and time.time() - cached[0] < RECAP_CACHE_SECONDS:
                recap = cached[3]
            else:
                recap = await RecapBuilder(community.bot, community.limits).build(
                    guild, start, end, community.store.optouts(guild.id)
                )
                if recap is None:
                    return "The server recap is not available right now."
                _recap_cache[key] = (time.time(), start, public, recap)
            # Checked after the last await: who hid themselves and which channels are public now.
            shown = _still_shown(guild, recap, community.store.optouts(guild.id))
            label = "This week so far" if period == "this_week" else "Last week"
            facts = recap_facts(shown, lambda title_id: community.title_name(guild.id, title_id))
            return f"{label} ({start.date().isoformat()} to {end.date().isoformat()}):\n{facts}"

        async def get_upcoming_birthdays(days: int = 30) -> str:
            """Lists the birthdays members saved on this server that fall in the next days.

            Call this when someone asks whose birthday is coming up.

            Args:
                days: How many days ahead to look, 1 to 30 (today included).

            Returns:
                One line per birthday, soonest first, as month/day and display name.
            """
            from cogs.community_lib.dates import upcoming_birthdays

            days = max(1, min(int(days or 30), 30))
            settings = community.store.get_settings(guild.id)
            today = community._local_now(settings).date()
            hidden = community.store.optouts(guild.id)
            lines = []
            for user_id, when in upcoming_birthdays(today, community.store.birthdays(guild.id), days):
                member = guild.get_member(user_id)
                if member is None or member.bot or user_id in hidden:
                    continue
                lines.append(f"{when.month}/{when.day}: <<<{member.display_name}>>>")
                if len(lines) >= MAX_BIRTHDAYS:
                    break
            if not lines:
                return f"No saved birthdays in the next {days} days."
            return f"Birthdays in the next {days} days (today is {today.month}/{today.day}):\n" + "\n".join(lines)

        async def set_my_stats_visibility(hide: bool) -> str:
            """Hides the person asking from rankings, recaps, achievement announcements and
            "who is playing" posts, or shows them again (the same as /leaderboard optout).

            Only call this when the person asking clearly wants it for themselves, e.g. "don't put
            me on the leaderboard". It can never change anyone else.

            Args:
                hide: True to hide, False to show again.

            Returns:
                What changed.
            """
            store = leaderboard.store
            store.set_optout(guild.id, message.author.id, bool(hide))
            if hide:
                return (
                    "Done: they are now hidden from rankings, recaps, achievement announcements and \"who is playing\" "
                    "posts. They can still see their own stats privately with /profile."
                )
            return "Done: they show up in rankings, recaps and announcements again."

        info = {"target_agent_mode": "info"}
        community_group = {**info, "tool_group": "community"}
        tools = []
        if leaderboard is not None:
            tools += [
                StructuredTool.from_function(coroutine=get_leaderboard, metadata=community_group),
                StructuredTool.from_function(coroutine=get_achievements, metadata=community_group),
                # Hiding oneself is a privacy control: it stays with the core tools everywhere.
                StructuredTool.from_function(coroutine=set_my_stats_visibility, metadata=info),
            ]
        if community is not None:
            tools.append(StructuredTool.from_function(coroutine=get_server_recap, metadata=community_group))
            try:
                birthdays_on = community.store.get_settings(guild.id).birthday_enabled
            except Exception:
                _logger.error("community tools: could not read the server's settings", exc_info=True)
                birthdays_on = False
            if birthdays_on:
                tools.append(StructuredTool.from_function(coroutine=get_upcoming_birthdays, metadata=community_group))
        return tools


class EventTools:
    """Tools over the events cog."""

    MAX_EVENTS = 10

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        self.runtime = runtime

    def get_tools(self) -> list:
        runtime = self.runtime
        message = getattr(runtime, "message", None)
        guild = getattr(message, "guild", None)
        bot = getattr(runtime, "bot", None)
        events = bot.get_cog("EventsCog") if bot is not None and hasattr(bot, "get_cog") else None
        if guild is None or events is None:
            return []

        async def list_upcoming_events() -> str:
            """Lists this server's upcoming events (made with /event create) that can be shown here.

            Call this when someone asks what events or meetups are planned, or how many people
            are going.

            Returns:
                One line per event: number, title, start time, how many are going, and its link.
                Start times are Discord timestamps such as <t:1700000000:F>; copy them as they are.
            """
            from addons.visibility import audience_can_read

            here = getattr(message, "channel", None)
            lines = []
            for event in events.store.upcoming(guild.id, time.time()):
                lookup = getattr(guild, "get_channel_or_thread", None) or guild.get_channel
                channel = lookup(event.channel_id)
                # Shown only where everyone reading this answer could also read the event's channel.
                if channel is None or not (channel.id == getattr(here, "id", None) or audience_can_read(channel)):
                    continue
                roster = events.store.roster(event)
                going = f"{len(roster.going)}/{event.capacity}" if event.capacity else str(len(roster.going))
                link = f"https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id}"
                lines.append(
                    f"#{event.id} <<<{event.title}>>> — starts <t:{int(event.starts_at)}:F> — going: {going}"
                    + (f", waiting: {len(roster.waiting)}" if roster.waiting else "")
                    + (f", maybe: {len(roster.maybe)}" if roster.maybe else "")
                    + f" — {link}"
                )
                if len(lines) >= self.MAX_EVENTS:
                    break
            if not lines:
                return "There are no upcoming events that can be shown here."
            return "Upcoming events:\n" + "\n".join(lines)

        return [
            StructuredTool.from_function(
                coroutine=list_upcoming_events, metadata={"target_agent_mode": "info", "tool_group": "events"}
            )
        ]
