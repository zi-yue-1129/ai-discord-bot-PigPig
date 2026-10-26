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

import discord
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
    quote: Optional[Dict[str, Any]] = None
    # The shareable channels everything was counted in.
    channel_ids: frozenset = frozenset()


async def read_recap(community: Any, guild: Any, start: datetime, end: datetime, hidden: Set[int], cache_key: Any) -> Optional[RecapView]:
    """Counts the week for the AI; None without message stats.

    Messages, talkers and titles only count shareable channels (everyone can read them, not
    NSFW), so nothing about private channels is told. Hidden members are left out of every
    count. Words and emojis are only kept per channel, not per member, so they are only shown
    when nobody on the server is hidden. The quote of the week (it fetches messages) is reused
    for ``RECAP_CACHE_SECONDS``; everything else is read on every call. Left out: regulars who
    went quiet (their last message may be in a private channel, so the list would tell), and the
    song of the week and DJ title (the play log does not record where a song was requested).
    """
    from cogs.community_lib.recap import (
        MAX_WORD_CHARS, TOP_CHANNELS, TOP_EMOJIS, TOP_TALKERS, TOP_WORDS, RecapBuilder, _visible,
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
    for title_id, _ in TITLES:
        if title_id in view.titles:
            lines.append(f"Title {title_name(title_id)}: {user_text(view.titles[title_id][0].display_name)}")
    return "\n".join(lines)


_BIRTHDAY_PROPOSALS = {
    "proposed": (
        "Posted a question with Save and Decline buttons for {name}. Nothing is saved until they press Save; "
        "do not say it is saved."
    ),
    "invalid_date": "That is not a real date. Ask for the right month and day.",
    "bot": "Bots do not have birthdays here.",
    "cannot_see": "{name} cannot see this channel, so they cannot be asked here.",
    "blocked": (
        "{name} cannot be asked about a birthday by other people. Do not retry; they can set it themselves with "
        "/birthday set or by asking you."
    ),
    "pending": "{name} already has a birthday question waiting for their answer.",
}


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
            hot words, quote of the week and the rotating titles (no music).

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

        async def get_upcoming_birthdays(days: Optional[int] = None) -> str:
            """Lists the birthdays members saved on this server that fall in the next days.

            Call this when someone asks whose birthday is coming up.

            Args:
                days: How many days ahead to look, 1 to 30 (today included); leave it out for 30.

            Returns:
                One line per birthday, soonest first, as month/day and display name.
            """
            from cogs.community_lib.dates import upcoming_birthdays

            days = max(1, min(int(30 if days is None else days), 30))
            # Read before get_settings, which creates the community database when it is missing.
            hidden = hidden_member_ids(runtime, guild.id)
            if hidden is None:
                return UNAVAILABLE
            settings = community.store.get_settings(guild.id)
            if not settings.birthday_enabled:
                return "Birthdays are turned off on this server (an admin can turn them on with /community birthdays)."
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

        async def remove_my_birthday() -> str:
            """Asks the person asking, with buttons, whether to delete the birthday they saved here.

            Only call this when the person asking clearly wants their own birthday removed. Nothing
            is deleted until they press Confirm themselves.

            Returns:
                Whether the question was posted.
            """
            result = await community.propose_birthday_removal(message.channel, message.author)
            return {
                "asked": "Posted a question with Confirm and Cancel buttons; it is only deleted when they press Confirm.",
                "none": "They had no birthday saved here.",
                "unavailable": UNAVAILABLE,
            }[result]

        async def propose_birthday(month: int, day: int, user_id: Optional[str] = None) -> str:
            """Asks a member, with buttons in this channel, whether to save a birthday for them here.

            Call this when someone asks you to remember or set a birthday on this server: their own
            or another member's. Nothing is saved unless that member presses Save themselves. If
            they decline a proposal made by someone else, later ones from other people are turned
            away until they ask for one themselves.

            Args:
                month: The birthday's month, 1-12.
                day: The birthday's day of the month.
                user_id: Optional Discord user ID or mention of the member whose birthday it is.
                    Defaults to the person asking.

            Returns:
                Whether the question was posted. The birthday is not saved yet: never say it is.
            """
            member, problem = _resolve_member(guild, user_id, message.author)
            if problem:
                return problem
            try:
                month, day = int(month), int(day)
            except (TypeError, ValueError):
                return "That is not a valid date."
            name = user_text(member.display_name)
            result = await community.propose_birthday(message.channel, message.author, member, month, day)
            return _BIRTHDAY_PROPOSALS.get(result, "Could not ask them.").format(name=name)

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
            # Whether birthdays are on is read when the tool is called: building the tool list must
            # not touch the database (it runs on the event loop for every message).
            tools.append(StructuredTool.from_function(coroutine=get_server_recap, metadata=community_group))
            tools.append(StructuredTool.from_function(coroutine=get_upcoming_birthdays, metadata=community_group))
            tools.append(StructuredTool.from_function(coroutine=remove_my_birthday, metadata=community_group))
            # Saving needs the member's own button press (see CommunityCog.propose_birthday).
            tools.append(StructuredTool.from_function(coroutine=propose_birthday, metadata=community_group))
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

        async def create_event(title: str, time: str, limit: int = 0, remind_minutes: int = 15) -> str:
            """Proposes an event people can sign up for, like /event create, with the person asking as host.

            The event is posted with a Confirm button that only the host can press; it is made
            only when they press it (within 3 minutes). Call this when someone asks to organise
            or schedule a get-together, game night, meetup, etc.

            Args:
                title: What the event is (up to 100 characters).
                time: When it starts, as they said it, e.g. "tomorrow 20:00", "Friday 9pm", "in 2 hours".
                limit: Most people who can join (others wait in line); 0 means no limit.
                remind_minutes: Minutes before the start to remind everyone going (0-1440).

            Returns:
                Whether the proposal was posted, or why not.
            """
            try:
                problem, draft = await events.post_draft(
                    message.channel, message.author, title, time, int(limit), int(remind_minutes)
                )
            except (TypeError, ValueError):
                return "limit and remind_minutes must be whole numbers."
            except discord.HTTPException:
                _logger.warning("create_event: could not post the proposal", exc_info=True)
                return "The event could not be posted in this channel."
            if problem is not None:
                return _EVENT_PROBLEMS.get(problem, "The event could not be made.")
            return (
                f"Posted the event {user_text(draft.title)} starting <t:{int(draft.starts_at)}:F> for confirmation. "
                "It is only created when the host presses Confirm within 3 minutes; tell them so."
            )

        async def join_event(event_id: int, status: str = "going") -> str:
            """Asks the person asking, with buttons, to confirm signing up for an event, marking
            themselves as maybe, or leaving it.

            Only call this when the person asking clearly wants it for themselves; it only ever
            changes the person asking, and only once they press Confirm. Use list_upcoming_events
            first if you do not know the event's number.

            Args:
                event_id: The event's number (shown as #N under the event).
                status: "going", "maybe" or "leave".

            Returns:
                Whether the question was posted.
            """
            from cogs.events_lib.store import GOING, MAYBE

            wanted = {"going": GOING, "maybe": MAYBE, "leave": None}
            status = str(status or "going").lower()
            if status not in wanted:
                return 'status must be "going", "maybe" or "leave".'
            try:
                event_id = int(str(event_id).lstrip("#"))
            except (TypeError, ValueError):
                return "Give the event's number, e.g. 12."
            problem = await events.propose_answer(message.channel, message.author, event_id, wanted[status])
            if problem is not None:
                return _EVENT_PROBLEMS.get(problem, "That event could not be changed.")
            return (
                f"Posted a question with Confirm and Cancel buttons for event #{event_id}. Nothing changes until "
                "they press Confirm within 3 minutes; tell them so."
            )

        events_group = {"target_agent_mode": "info", "tool_group": "events"}
        return [
            StructuredTool.from_function(coroutine=list_upcoming_events, metadata=events_group),
            StructuredTool.from_function(coroutine=create_event, metadata=events_group),
            StructuredTool.from_function(coroutine=join_event, metadata=events_group),
        ]


_EVENT_PROBLEMS = {
    "invalid_title": "The title must be 1 to 100 characters.",
    "invalid_limit": "limit must be between 0 and 100.",
    "invalid_remind": "remind_minutes must be between 0 and 1440.",
    "invalid_time": 'Could not understand the time; ask for something like "tomorrow 20:00" or "in 2 hours".',
    "past_time": "That time has already passed; events must start in the future.",
    "too_far": "Events can be at most 180 days ahead.",
    "user_limit": "They already host 5 upcoming events; one must end or be cancelled first.",
    "guild_limit": "This server already has 25 upcoming events.",
    "draft_limit": "Too many event proposals on this server are waiting for confirmation; try again later.",
    "not_found": "There is no such event here (or they cannot see its channel).",
    "event_gone": "That event was cancelled or no longer exists.",
    "event_started": "That event has already started, so sign-ups are closed.",
}
