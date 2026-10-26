"""The weekly server recap: when it is due, the numbers in it and how they are laid out.

All numbers are computed here from the stats the bot already keeps; the model only adds
an optional news paragraph on top (see ``CommunityCog.post_weekly_recap``). Members who
opted out of rankings are never named, quoted or given a title.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import discord

from addons.logging import get_logger
from addons.visibility import audience_can_read
from cogs.memory.db.stats_storage import MAX_WORD_CHARS, week_start

from .limits import CommunityLimits

logger = get_logger(server_id="Bot", source=__name__)

# A late recap is still posted this long after its scheduled time (the bot was down), not later.
CATCH_UP = timedelta(hours=24)
TOP_CHANNELS = 3
TOP_TALKERS = 3
TOP_EMOJIS = 5
TOP_WORDS = 5
QUOTE_CHARS = 200
# Discord refuses an embed field value longer than this.
FIELD_CHARS = 1024
# A song of the week needs this many plays and fewer than half of them skipped.
MIN_SONG_PLAYS = 2
# Rotating titles, in the order shown.
TITLES = [("talker", "🎤"), ("night_owl", "🌙"), ("funny", "😂"), ("dj", "🎧")]


def recap_week_due(local: datetime, day: int, hour: int) -> Optional[datetime]:
    """Returns the local Monday 00:00 of the week whose recap is due at ``local``, if any.

    The recap of a week is due from its ``day`` at ``hour`` until ``CATCH_UP`` later.
    """
    monday = local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=local.weekday())
    moment = monday + timedelta(days=day, hours=hour)
    if local < moment:
        monday -= timedelta(days=7)
        moment -= timedelta(days=7)
    return monday if local - moment <= CATCH_UP else None


@dataclass
class Recap:
    """One week's recap numbers; people are guild members, already filtered."""

    week: str
    start: datetime
    end: datetime
    total: int = 0
    previous_total: int = 0
    channels: List[Tuple[Any, int]] = field(default_factory=list)
    talkers: List[Tuple[Any, int]] = field(default_factory=list)
    emojis: List[Tuple[str, int]] = field(default_factory=list)
    words: List[Tuple[str, int]] = field(default_factory=list)
    quote: Optional[Dict[str, Any]] = None
    song: Optional[Tuple[str, str, int]] = None
    titles: Dict[str, Tuple[Any, int]] = field(default_factory=dict)
    missing: List[Tuple[Any, int]] = field(default_factory=list)


def _total_without(rows: Sequence[Tuple[Any, int]], hidden: Set[int]) -> int:
    """The sum of ``(user_id, count)`` rows, leaving out the hidden members' (a row whose id is no
    number cannot be told apart and is counted)."""
    total = 0
    for user_id, count in rows:
        try:
            if int(user_id) in hidden:
                continue
        except (TypeError, ValueError):
            pass
        total += int(count)
    return total


def _visible(guild: Any, rows: Sequence[Tuple[Any, int]], hidden: Set[int], limit: Optional[int] = None) -> List[Tuple[Any, int]]:
    """Turns ``(user_id, value)`` rows into ``(member, value)`` for current, human, not hidden members."""
    found = []
    for user_id, value in rows:
        try:
            member_id = int(user_id)
        except (TypeError, ValueError):
            continue
        member = guild.get_member(member_id)
        if member is None or member.bot or member_id in hidden:
            continue
        found.append((member, int(value)))
        if limit is not None and len(found) >= limit:
            break
    return found


def is_public(guild: Any, channel: Any) -> bool:
    """Whether every member can see ``channel`` and read its history (see ``audience_can_read``).

    ``@everyone`` must be allowed, and no role or member overwrite may deny it; private threads
    and anything that cannot be established count as not public.
    """
    return audience_can_read(channel)


def public_channel_ids(guild: Any) -> List[str]:
    """The ids of the channels and (public) threads every member can read."""
    found = [c for c in getattr(guild, "channels", []) if is_public(guild, c)]
    found += [t for t in getattr(guild, "threads", []) if is_public(guild, t)]
    return [str(c.id) for c in found]


def _field(text: str) -> str:
    """Cuts an embed field value to what Discord accepts."""
    return text if len(text) <= FIELD_CHARS else text[: FIELD_CHARS - 1] + "…"


def _parse_time(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class RecapBuilder:
    """Collects a week's numbers from the stats collector, StatsCog's storage and the music log."""

    def __init__(self, bot: Any, limits: CommunityLimits) -> None:
        self.bot = bot
        self.limits = limits

    def _stats_storage(self) -> Any:
        cog = self.bot.get_cog("StatsCog") if hasattr(self.bot, "get_cog") else None
        return getattr(cog, "stats_storage", None)

    def _taste_store(self) -> Any:
        cog = self.bot.get_cog("YTMusic") if hasattr(self.bot, "get_cog") else None
        return getattr(cog, "_taste_store", None)

    async def build(self, guild: Any, start: datetime, end: datetime, hidden: Set[int]) -> Optional[Recap]:
        """Gathers the recap of ``[start, end)``; None when the message stats are unavailable."""
        collector = getattr(self.bot, "stats_collector", None)
        if collector is None:
            return None
        gid = str(guild.id)
        since, until = start.timestamp(), end.timestamp()
        recap = Recap(week=week_start(start), start=start, end=end)

        per_user = await collector.message_counts_by_user(gid, since, until)
        # What hidden members wrote is not counted either: the total would give them away.
        recap.total = _total_without(per_user, hidden)
        recap.previous_total = _total_without(
            await collector.message_counts_by_user(gid, since - 7 * 86400, until - 7 * 86400), hidden
        )
        recap.talkers = _visible(guild, per_user, hidden, TOP_TALKERS)
        for channel_id, count in await collector.message_counts_by_channel(gid, since, until):
            channel = guild.get_channel(int(channel_id)) if str(channel_id).isdigit() else None
            if channel is not None and is_public(guild, channel):
                recap.channels.append((channel, count))
            if len(recap.channels) >= TOP_CHANNELS:
                break
        if recap.talkers:
            recap.titles["talker"] = recap.talkers[0]
        offset = (start.utcoffset() or timedelta()).total_seconds()
        night = _visible(guild, await collector.night_counts_by_user(gid, since, until, offset), hidden, 1)
        if night:
            recap.titles["night_owl"] = night[0]

        storage = self._stats_storage()
        if storage is not None:
            # Only what was said where everyone can read it goes into a public post.
            public = public_channel_ids(guild)
            recap.emojis = await storage.get_weekly_terms(gid, recap.week, "emoji", TOP_EMOJIS, public)
            # Words counted before the length cap existed are skipped here too.
            words = await storage.get_weekly_terms(gid, recap.week, "word", TOP_WORDS * 4, public)
            recap.words = [(w, n) for w, n in words if len(w) <= MAX_WORD_CHARS][:TOP_WORDS]
            funny = _visible(guild, await storage.reactions_by_author(gid, since, until), hidden, 1)
            if funny:
                recap.titles["funny"] = funny[0]
            recap.quote = await self._quote(guild, storage, since, until, hidden)
            recap.missing = await self._missing(guild, storage, end, hidden)

        taste = self._taste_store()
        if taste is not None:
            for video_id, title, plays, skips in taste.top_played(guild.id, since, until, 5):
                if plays >= MIN_SONG_PLAYS and (skips or 0) * 2 < plays:
                    recap.song = (video_id, title, plays)
                    break
            dj = _visible(guild, taste.top_requesters(guild.id, since, until, 10), hidden, 1)
            if dj:
                recap.titles["dj"] = dj[0]
        return recap

    async def _quote(self, guild: Any, storage: Any, since: float, until: float, hidden: Set[int]) -> Optional[Dict[str, Any]]:
        """The most reacted message of the week that is still there, in a channel everyone can read, by a visible member."""
        for row in await storage.get_top_reacted_messages(str(guild.id), since, until, 10):
            author = _visible(guild, [(row["author_id"], row["count"])], hidden)
            lookup = getattr(guild, "get_channel_or_thread", None) or guild.get_channel
            channel = lookup(int(row["channel_id"])) if str(row["channel_id"]).isdigit() else None
            # The bot can read private channels; their messages must not end up in a public post.
            if not author or channel is None or not is_public(guild, channel):
                continue
            try:
                message = await channel.fetch_message(int(row["message_id"]))
            except (discord.HTTPException, AttributeError):
                continue  # deleted, or the bot can no longer read the channel
            content = (message.content or "").strip()
            if not content:
                continue
            if len(content) > QUOTE_CHARS:
                content = content[: QUOTE_CHARS - 1] + "…"
            return {"member": author[0][0], "content": content, "url": message.jump_url, "count": row["count"]}
        return None

    async def _missing(self, guild: Any, storage: Any, now: datetime, hidden: Set[int]) -> List[Tuple[Any, int]]:
        """Former regulars who have been silent for ``missing_after_days`` or more, as ``(member, days)``."""
        if self.limits.missing_max <= 0:
            return []
        found = []
        for row in await storage.get_regulars(str(guild.id), self.limits.missing_min_messages):
            last = _parse_time(row.get("last_active_at"))
            if last is None:
                continue
            days = (now - last).days
            if days < self.limits.missing_after_days:
                continue
            visible = _visible(guild, [(row["user_id"], days)], hidden)
            if visible:
                found.append(visible[0])
            if len(found) >= self.limits.missing_max:
                break
        return found


def format_recap(recap: Recap, t: Callable[..., str], title_name: Callable[[str], str], guild_name: str, report: Optional[str]) -> discord.Embed:
    """Lays a recap out as an embed; ``t(key, **kwargs)`` translates a community response."""
    embed = discord.Embed(title=t("weekly_title", guild=guild_name), description=report or t("weekly_intro", total=f"{recap.total:,}"))
    if recap.previous_total:
        change = round((recap.total - recap.previous_total) * 100 / recap.previous_total)
        trend = t("weekly_trend", change=f"{change:+d}%", previous=f"{recap.previous_total:,}")
    else:
        trend = ""
    embed.add_field(name=t("weekly_messages"), value=_field(f"**{recap.total:,}** {trend}".strip()), inline=False)
    if recap.channels:
        embed.add_field(name=t("weekly_channels"), value=_field("\n".join(f"{c.mention} · {n:,}" for c, n in recap.channels)), inline=True)
    if recap.talkers:
        embed.add_field(name=t("weekly_talkers"), value=_field("\n".join(f"{m.mention} · {n:,}" for m, n in recap.talkers)), inline=True)
    if recap.emojis:
        embed.add_field(name=t("weekly_emojis"), value=_field(" ".join(f"{e}×{n}" for e, n in recap.emojis)), inline=False)
    if recap.words:
        embed.add_field(name=t("weekly_words"), value=_field("、".join(w for w, _ in recap.words)), inline=False)
    if recap.quote:
        quote = recap.quote
        embed.add_field(
            name=t("weekly_quote", count=quote["count"]),
            value=_field(f"> {quote['content']}\n— {quote['member'].mention} · [{t('weekly_jump')}]({quote['url']})"),
            inline=False,
        )
    if recap.song:
        video_id, title, plays = recap.song
        embed.add_field(
            name=t("weekly_song"), value=_field(f"[{title or video_id}](https://www.youtube.com/watch?v={video_id}) · {t('weekly_plays', count=plays)}"), inline=False
        )
    if recap.titles:
        lines = [f"{emoji} {title_name(title_id)}：{recap.titles[title_id][0].mention}" for title_id, emoji in TITLES if title_id in recap.titles]
        embed.add_field(name=t("weekly_titles"), value=_field("\n".join(lines)), inline=False)
    if recap.missing:
        lines = [t("weekly_missing_line", name=m.mention, days=days) for m, days in recap.missing]
        embed.add_field(name=t("weekly_missing"), value=_field("\n".join(lines)), inline=False)
    return embed


def recap_facts(recap: Recap, title_name: Callable[[str], str]) -> str:
    """The recap's numbers as plain facts for the model; names and quotes are wrapped as user data."""
    lines = [f"Messages this week: {recap.total} (last week: {recap.previous_total})"]
    if recap.channels:
        lines.append("Busiest channels: " + ", ".join(f"<<<#{getattr(c, 'name', c)}>>> ({n})" for c, n in recap.channels))
    if recap.talkers:
        lines.append("Most talkative: " + ", ".join(f"<<<{m.display_name}>>> ({n})" for m, n in recap.talkers))
    if recap.emojis:
        lines.append("Top emojis: " + " ".join(e for e, _ in recap.emojis))
    if recap.words:
        lines.append("Hot words: <<<" + ", ".join(w for w, _ in recap.words) + ">>>")
    if recap.quote:
        lines.append(f"Quote of the week by <<<{recap.quote['member'].display_name}>>>: <<<{recap.quote['content']}>>>")
    if recap.song:
        lines.append(f"Song of the week: <<<{recap.song[1]}>>> ({recap.song[2]} plays)")
    for title_id, _ in TITLES:
        if title_id in recap.titles:
            lines.append(f"Title {title_name(title_id)}: <<<{recap.titles[title_id][0].display_name}>>>")
    if recap.missing:
        lines.append("Missing regulars: " + ", ".join(f"<<<{m.display_name}>>> ({d} days silent)" for m, d in recap.missing))
    return "\n".join(lines)
