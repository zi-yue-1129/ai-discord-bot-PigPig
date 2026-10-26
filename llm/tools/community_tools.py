"""Community tools for LLM integration: rankings, achievements, the weekly recap and birthdays.

Every answer the model writes is posted in the channel for everyone there to read, so these
tools only return what the matching public post would show: members who hid themselves with
``/leaderboard optout`` are never named, and anything said in a channel is only used when every
member can read that channel. Names and other text members wrote are wrapped in ``<<< >>>`` so
the model treats them as data.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, TYPE_CHECKING

from langchain_core.tools.structured import StructuredTool

from addons.logging import get_logger
from llm.tools.user_stats import _is_hidden, hidden_member_ids

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_logger = get_logger(server_id="Bot", source="llm.tools.community_tools")

# How long the recap's quote of the week is reused: finding it fetches messages from Discord.
RECAP_CACHE_SECONDS = 600
MAX_BIRTHDAYS = 15
USER_TEXT_CHARS = 100
UNAVAILABLE = "This is not available right now."
# guild id, period -> (read at, local start, quote of the week)
_recap_cache: Dict[Tuple[int, str], Tuple[float, datetime, Any]] = {}

_MASS_MENTION = re.compile(r"@(everyone|here)", re.IGNORECASE)
_LINK = re.compile(r"(https?://|www\.|discord\.gg/)\S*", re.IGNORECASE)


def user_text(text: Any, limit: int = USER_TEXT_CHARS) -> str:
    """Text a member wrote, made safe to hand to the model and wrapped in ``<<< >>>``.

    Angle brackets are replaced so the text cannot close the wrapper (or form a mention),
    ``@everyone``/``@here`` are broken up, links are dropped and the text is cut to ``limit``.
    """
    text = str(text or "").replace("<", "‹").replace(">", "›")
    text = _MASS_MENTION.sub("@\u200b\\1", text)
    text = _LINK.sub("[link]", text)
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return f"<<<{text}>>>"


def _named(member: Any) -> Any:
    """A stand-in for ``member`` whose display name is safe user text, for the cogs' text builders."""
    return SimpleNamespace(id=member.id, display_name=user_text(member.display_name))


def _is_nsfw(channel: Any) -> bool:
    for current in (channel, getattr(channel, "parent", None)):
        check = getattr(current, "is_nsfw", None)
        if callable(check):
            try:
                if check():
                    return True
            except Exception:
                return True
    return False


def shareable(channel: Any) -> bool:
    """Whether what happened in ``channel`` may be retold in any channel of the server.

    Everyone must be able to read it (``audience_can_read``) and it must not be age-restricted
    (NSFW, its own or its parent's).
    """
    from addons.visibility import audience_can_read

    return channel is not None and audience_can_read(channel) and not _is_nsfw(channel)


def shareable_channels(guild: Any) -> Dict[str, Any]:
    """The server's shareable channels and threads, by id."""
    found = list(getattr(guild, "channels", []) or []) + list(getattr(guild, "threads", []) or [])
    return {str(c.id): c for c in found if shareable(c)}


def _total_without(rows: Sequence[Tuple[Any, int]], hidden: Set[int]) -> int:
    """The sum of ``(user_id, count)`` rows, leaving out hidden members' rows."""
    total = 0
    for user_id, count in rows:
        try:
            if int(user_id) in hidden:
                continue
        except (TypeError, ValueError):
            pass
        total += int(count)
    return total


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


@dataclass
class RecapView:
    """One week as the AI may tell it: counted only in shareable channels, without hidden members."""

    total: int = 0
    previous_total: int = 0
    channels: List[Tuple[Any, int]] = field(default_factory=list)
    talkers: List[Tuple[Any, int]] = field(default_factory=list)
    titles: Dict[str, Tuple[Any, int]] = field(default_factory=dict)
    emojis: List[Tuple[str, int]] = field(default_factory=list)
    words: List[Tuple[str, int]] = field(default_factory=list)
    song: Optional[Tuple[str, str, int]] = None
    quote: Optional[Dict[str, Any]] = None
    # The shareable channels everything was counted in.
    channel_ids: frozenset = frozenset()


async def read_recap(community: Any, guild: Any, start: datetime, end: datetime, hidden: Set[int], cache_key: Any) -> Optional[RecapView]:
    """Counts the week for the AI; None without message stats.

    Messages, talkers and titles only count shareable channels (everyone can read them, not
    NSFW), so nothing about private channels is told. Hidden members are left out of every
    count. Words and emojis are only kept per channel, not per member, so they are only shown
    when nobody on the server is hidden. The quote of the week (it fetches messages) is reused
    for ``RECAP_CACHE_SECONDS``; everything else is read on every call. Regulars who went quiet
    are left out: their last message may be in a private channel, so the list would tell.
    """
    from cogs.community_lib.recap import (
        MAX_WORD_CHARS, MIN_SONG_PLAYS, TOP_CHANNELS, TOP_EMOJIS, TOP_TALKERS, TOP_WORDS, RecapBuilder, _visible,
    )
    from cogs.memory.db.stats_storage import week_start

    bot = community.bot
    collector = getattr(bot, "stats_collector", None)
    if collector is None:
        return None
    gid = str(guild.id)
    since, until = start.timestamp(), end.timestamp()
    public = shareable_channels(guild)
    ids = list(public)
    view = RecapView(channel_ids=frozenset(ids))

    per_user = await collector.message_counts_by_user(gid, since, until, channel_ids=ids)
    view.total = _total_without(per_user, hidden)
    view.previous_total = _total_without(
        await collector.message_counts_by_user(gid, since - 7 * 86400, until - 7 * 86400, channel_ids=ids), hidden
    )
    view.talkers = _visible(guild, per_user, hidden, TOP_TALKERS)
    if view.talkers:
        view.titles["talker"] = view.talkers[0]
    for channel_id, count in await collector.message_counts_by_channel(gid, since, until, exclude_user_ids=hidden):
        channel = public.get(str(channel_id))
        if channel is not None and count:
            view.channels.append((channel, int(count)))
        if len(view.channels) >= TOP_CHANNELS:
            break
    offset = (start.utcoffset() or timedelta()).total_seconds()
    night = _visible(guild, await collector.night_counts_by_user(gid, since, until, offset, channel_ids=ids), hidden, 1)
    if night:
        view.titles["night_owl"] = night[0]

    cog = bot.get_cog("StatsCog") if hasattr(bot, "get_cog") else None
    storage = getattr(cog, "stats_storage", None)
    if storage is not None:
        if ids and not hidden:
            week = week_start(start)
            view.emojis = await storage.get_weekly_terms(gid, week, "emoji", TOP_EMOJIS, ids)
            words = await storage.get_weekly_terms(gid, week, "word", TOP_WORDS * 4, ids)
            view.words = [(w, n) for w, n in words if len(w) <= MAX_WORD_CHARS][:TOP_WORDS]
        funny = _visible(guild, await storage.reactions_by_author(gid, since, until, channel_ids=ids), hidden, 1)
        if funny:
            view.titles["funny"] = funny[0]
        builder = RecapBuilder(bot, community.limits)
        cached = _recap_cache.get(cache_key)
        if cached and cached[1] == start and time.time() - cached[0] < RECAP_CACHE_SECONDS:
            view.quote = cached[2]
        else:
            view.quote = await builder._quote(guild, storage, since, until, hidden)
            _recap_cache[cache_key] = (time.time(), start, view.quote)

    music = bot.get_cog("YTMusic") if hasattr(bot, "get_cog") else None
    taste = getattr(music, "_taste_store", None)
    if taste is not None:
        for video_id, title, plays, skips in taste.top_played(guild.id, since, until, 5, exclude_requesters=hidden):
            if plays >= MIN_SONG_PLAYS and (skips or 0) * 2 < plays:
                view.song = (video_id, title, plays)
                break
        dj = _visible(guild, taste.top_requesters(guild.id, since, until, 10), hidden, 1)
        if dj:
            view.titles["dj"] = dj[0]
    return view


def _still_shown(guild: Any, view: RecapView, hidden: set) -> RecapView:
    """``view`` without what may no longer be shown: hidden or departed members, and a quote from a
    channel that stopped being shareable."""
    from copy import copy

    def visible(member: Any) -> bool:
        return member is not None and member.id not in hidden and guild.get_member(member.id) is not None

    shown = copy(view)
    shown.talkers = [(m, n) for m, n in view.talkers if visible(m)]
    shown.titles = {key: (m, n) for key, (m, n) in view.titles.items() if visible(m)}
    quote = view.quote
    if quote and not (visible(quote["member"]) and shareable(_quote_channel(guild, quote["url"]))):
        quote = None
    shown.quote = quote
    return shown


def recap_text(view: RecapView, title_name: Any) -> str:
    """The recap as plain facts for the model; everything members wrote goes through ``user_text``."""
    from cogs.community_lib.recap import TITLES

    lines = [
        f"Messages this week in channels everyone can read: {view.total} (last week: {view.previous_total})"
    ]
    if view.channels:
        lines.append(
            "Busiest channels: " + ", ".join(f"{user_text('#' + str(getattr(c, 'name', c)))} ({n})" for c, n in view.channels)
        )
    if view.talkers:
        lines.append("Most talkative: " + ", ".join(f"{user_text(m.display_name)} ({n})" for m, n in view.talkers))
    if view.emojis:
        lines.append("Top emojis: " + " ".join(user_text(e, 40) for e, _ in view.emojis))
    if view.words:
        lines.append("Hot words: " + ", ".join(user_text(w, 40) for w, _ in view.words))
    if view.quote:
        lines.append(
            f"Quote of the week by {user_text(view.quote['member'].display_name)}: {user_text(view.quote['content'], 200)}"
        )
    if view.song:
        lines.append(f"Song of the week: {user_text(view.song[1] or view.song[0])} ({view.song[2]} plays)")
    for title_id, _ in TITLES:
        if title_id in view.titles:
            lines.append(f"Title {title_name(title_id)}: {user_text(view.titles[title_id][0].display_name)}")
    return "\n".join(lines)


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
            # Read before the ranking, which may create the community database (it reads the
            # server's time zone), and again after it: members may have hidden themselves meanwhile.
            if hidden_member_ids(runtime, guild.id) is None:
                return UNAVAILABLE
            ranked = await leaderboard.rankings(guild, kind, period)
            if ranked is None:
                return "The leaderboard is not available right now."
            hidden = hidden_member_ids(runtime, guild.id)
            if hidden is None:
                return UNAVAILABLE
            ranked = [(_named(m), v) for m, v in ranked if m.id not in hidden]
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
            return leaderboard.achievements_text(guild.id, _named(member))

        async def get_server_recap(period: str = "this_week") -> str:
            """Summarises the server's week: message count, busiest public channels, top talkers,
            hot words, quote and song of the week and the rotating titles.

            Call this when someone asks how the server's week went, what was popular, or who holds
            a title such as the week's top talker.

            Args:
                period: "this_week" (so far) or "last_week".

            Returns:
                The facts, one per line; text members wrote is wrapped in <<< >>>.
            """
            period = period if period in ("this_week", "last_week") else "this_week"
            # Read before anything that may create the community database (get_settings does).
            hidden = hidden_member_ids(runtime, guild.id)
            if hidden is None:
                return UNAVAILABLE
            settings = community.store.get_settings(guild.id)
            local = community._local_now(settings)
            monday = local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=local.weekday())
            start, end = (monday, local) if period == "this_week" else (monday - timedelta(days=7), monday)
            view = await read_recap(community, guild, start, end, hidden, (guild.id, period))
            if view is None:
                return "The server recap is not available right now."
            # Checked after the last await: who is hidden and which channels are shareable now.
            hidden_now = hidden_member_ids(runtime, guild.id)
            if hidden_now is None or hidden_now - hidden:
                # Someone hid themselves while the week was counted: they may still be in it.
                return UNAVAILABLE
            if not view.channel_ids <= frozenset(shareable_channels(guild)):
                # A channel stopped being shareable while it was counted.
                return UNAVAILABLE
            shown = _still_shown(guild, view, hidden_now)
            label = "This week so far" if period == "this_week" else "Last week"
            facts = recap_text(shown, lambda title_id: community.title_name(guild.id, title_id))
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
            # Read before get_settings, which creates the community database when it is missing.
            hidden = hidden_member_ids(runtime, guild.id)
            if hidden is None:
                return UNAVAILABLE
            settings = community.store.get_settings(guild.id)
            today = community._local_now(settings).date()
            lines = []
            for user_id, when in upcoming_birthdays(today, community.store.birthdays(guild.id), days):
                member = guild.get_member(user_id)
                if member is None or member.bot or user_id in hidden:
                    continue
                lines.append(f"{when.month}/{when.day}: {user_text(member.display_name)}")
                if len(lines) >= MAX_BIRTHDAYS:
                    break
            if not lines:
                return f"No saved birthdays in the next {days} days."
            return f"Birthdays in the next {days} days (today is {today.month}/{today.day}):\n" + "\n".join(lines)

        async def hide_my_stats() -> str:
            """Hides the person asking from rankings, recaps, achievement announcements and
            "who is playing" posts (the same as /leaderboard optout hide:True).

            Only call this when the person asking clearly wants it for themselves, e.g. "don't put
            me on the leaderboard". It can never change anyone else. Showing someone again is not
            possible from chat: they run /leaderboard optout hide:False themselves.

            Returns:
                What changed.
            """
            leaderboard.store.set_optout(guild.id, message.author.id, True)
            return (
                "Done: they are now hidden from rankings, recaps, achievement announcements and \"who is playing\" "
                "posts. They can still see their own stats privately with /profile, and show up again with "
                "/leaderboard optout hide:False."
            )

        info = {"target_agent_mode": "info"}
        community_group = {**info, "tool_group": "community"}
        tools = []
        if leaderboard is not None:
            tools += [
                StructuredTool.from_function(coroutine=get_leaderboard, metadata=community_group),
                StructuredTool.from_function(coroutine=get_achievements, metadata=community_group),
                # Hiding oneself is a privacy control: it stays with the core tools everywhere.
                StructuredTool.from_function(coroutine=hide_my_stats, metadata=info),
            ]
        if community is not None:
            tools.append(StructuredTool.from_function(coroutine=get_server_recap, metadata=community_group))
            try:
                # get_settings creates the community database when it is missing, which would turn
                # an unreadable opt-out list into an empty one: only read it once the list is there.
                readable = hidden_member_ids(runtime, guild.id) is not None
                birthdays_on = readable and community.store.get_settings(guild.id).birthday_enabled
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
            here = getattr(message, "channel", None)
            # Who signed up is counted without hidden members and people who left; unreadable
            # opt-outs leave the counts out.
            hidden = hidden_member_ids(runtime, guild.id)
            lines = []
            for event in events.store.upcoming(guild.id, time.time()):
                lookup = getattr(guild, "get_channel_or_thread", None) or guild.get_channel
                channel = lookup(event.channel_id)
                # Shown only where everyone reading this answer could also read the event's channel.
                if channel is None or not (channel.id == getattr(here, "id", None) or shareable(channel)):
                    continue
                link = f"https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id}"
                line = f"#{event.id} {user_text(event.title)} — starts <t:{int(event.starts_at)}:F>"
                if hidden is not None:
                    roster = events.store.roster(event)

                    def counted(user_ids: List[int]) -> int:
                        return sum(1 for u in user_ids if u not in hidden and guild.get_member(u) is not None)

                    going, waiting, maybe = counted(roster.going), counted(roster.waiting), counted(roster.maybe)
                    line += f" — going: {going}" + (f" (capacity {event.capacity})" if event.capacity else "")
                    line += (f", waiting: {waiting}" if waiting else "") + (f", maybe: {maybe}" if maybe else "")
                lines.append(f"{line} — {link}")
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
