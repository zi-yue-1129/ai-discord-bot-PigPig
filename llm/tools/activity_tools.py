"""Tools for what the server is doing together: starting a game, who plays what, the most played songs.

Like the other community tools, answers are posted for everyone in the channel: members hidden
with ``/leaderboard optout`` are never named or counted (and nobody is when the list cannot be
read), only members who can see the channel are named, songs only count when they played where
everyone could hear them, and names and titles go through ``user_text()``. Building the tool
list reads no database. Starting a game only posts a Start button that the asker must press.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from langchain_core.tools.structured import StructuredTool

from addons.logging import get_logger
from llm.tools.community_tools import UNAVAILABLE, shareable, user_text
from llm.tools.user_stats import hidden_member_ids

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_logger = get_logger(server_id="Bot", source="llm.tools.activity_tools")

MAX_GAMES = 10
MAX_NAMES = 5
MAX_SONGS = 10
_PERIOD_DAYS = {"week": 7, "month": 30}


def _cog(runtime: Any, name: str) -> Any:
    bot = getattr(runtime, "bot", None)
    return bot.get_cog(name) if bot is not None and hasattr(bot, "get_cog") else None


class GameTools:
    """Starts the server games (/game quiz, chain, guess_song) for the person asking."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        self.runtime = runtime

    def get_tools(self) -> list:
        runtime = self.runtime
        message = getattr(runtime, "message", None)
        guild = getattr(message, "guild", None)
        games = _cog(runtime, "GamesCog")
        if guild is None or games is None:
            return []

        async def start_server_game(
            game: str, rounds: int = 5, homophones: bool = False, days: Optional[int] = None, this_channel: bool = False
        ) -> str:
            """Offers a game in this channel with the person asking as host, like /game.

            Games: "quiz" (questions about things that happened on this server), "chain" (word
            chain: each word starts with the last character of the one before) and "guess_song"
            (guess songs the server listened to from short clips; the host must be in a voice
            channel). Only call this when the person asking wants to play one of them. It posts a
            Start button only they can press; the game begins when they press it.

            Args:
                game: "quiz", "chain" or "guess_song".
                rounds: Questions or songs, 3 to 10 (not used by "chain").
                homophones: Chain only: also accept a character with the same pronunciation (Chinese).
                days: Quiz only: only use memories from the last this many days.
                this_channel: Quiz only: only use memories from this channel.

            Returns:
                That the Start button is posted, or why the game cannot start.
            """
            game = str(game or "").lower().replace(" ", "_")
            if game not in ("quiz", "chain", "guess_song"):
                return 'game must be "quiz", "chain" or "guess_song".'
            try:
                problem = await games.offer_game(
                    game, guild, message.channel, message.author, int(rounds or 5),
                    homophones=bool(homophones), days=int(days) if days else None, this_channel=bool(this_channel),
                )
            except (TypeError, ValueError):
                return "rounds and days must be whole numbers."
            if problem is not None:
                return f"The game could not start: {problem}"
            return (
                f"Posted a Start button for the {game.replace('_', ' ')} game; it begins when the asker presses it "
                "(within 2 minutes). Keep your reply short."
            )

        return [
            StructuredTool.from_function(
                coroutine=start_server_game, metadata={"target_agent_mode": "info", "tool_group": "games"}
            )
        ]


class PlayingTools:
    """Who on the server is playing which game right now (when "what everyone is playing" is on)."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        self.runtime = runtime

    def get_tools(self) -> list:
        runtime = self.runtime
        message = getattr(runtime, "message", None)
        guild = getattr(message, "guild", None)
        playing = _cog(runtime, "PlayingCog")
        if guild is None or playing is None:
            return []

        async def who_is_playing() -> str:
            """Lists the games members of this server are playing right now and who plays them.

            Call this when someone asks what people are playing, or who is playing a game.

            Returns:
                One line per game, most players first: the game, how many play it and their names.
            """
            here = message.channel
            # Read before the settings, which may create the community database, and fail closed.
            hidden = hidden_member_ids(runtime, guild.id)
            if hidden is None:
                return UNAVAILABLE
            try:
                if not playing._feature_on(guild.id):
                    return 'Showing what members are playing is turned off on this server (/community playing).'
            except Exception:
                _logger.error("who_is_playing: could not read the server's settings", exc_info=True)
                return UNAVAILABLE
            found: List[tuple] = []
            for group in playing.tracker.groups(guild.id, time.time(), 0):
                # Only members who can see this channel, are not bots and did not hide themselves;
                # hidden members are not counted either.
                players = playing._players(guild, here, group, hidden)
                if not players:
                    continue
                names = ", ".join(user_text(member.display_name) for member in players[:MAX_NAMES])
                more = f" and {len(players) - MAX_NAMES} more" if len(players) > MAX_NAMES else ""
                found.append((len(players), f"{user_text(group.name)}: {len(players)} playing ({names}{more})"))
            if not found:
                return "Nobody here is playing a game right now (as far as Discord shows)."
            # Most players first, counting only the members who may be named here.
            found.sort(key=lambda item: -item[0])
            return "Playing right now:\n" + "\n".join(line for _, line in found[:MAX_GAMES])

        return [
            StructuredTool.from_function(
                coroutine=who_is_playing, metadata={"target_agent_mode": "info", "tool_group": "playing"}
            )
        ]


class PopularSongTools:
    """The songs played most on this server, from the music player's play log."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        self.runtime = runtime

    def get_tools(self) -> list:
        runtime = self.runtime
        message = getattr(runtime, "message", None)
        guild = getattr(message, "guild", None)
        music = _cog(runtime, "YTMusic")
        taste = getattr(music, "_taste_store", None)
        if guild is None or taste is None or not hasattr(taste, "plays_with_places"):
            return []
        here_id = getattr(getattr(message, "channel", None), "id", None)

        async def get_popular_songs(period: str = "week", limit: int = 5) -> str:
            """Lists the songs played most on this server recently (only songs everyone could hear).

            Call this when someone asks what the server has been listening to or which songs are
            popular. To play one, use play_music with its title.

            Args:
                period: "week" (last 7 days) or "month" (last 30 days).
                limit: How many songs, 1 to 10.

            Returns:
                One line per song: title, plays and how often it was skipped.
            """
            days = _PERIOD_DAYS.get(str(period), 7)
            try:
                limit = max(1, min(int(limit or 5), MAX_SONGS))
            except (TypeError, ValueError):
                limit = 5
            hidden = hidden_member_ids(runtime, guild.id)
            if hidden is None:
                return UNAVAILABLE
            now = time.time()
            try:
                rows = taste.plays_with_places(guild.id, now - days * 86400, now + 1)
            except Exception:
                _logger.error("get_popular_songs: could not read the play log", exc_info=True)
                return UNAVAILABLE
            lookup = getattr(guild, "get_channel_or_thread", None) or guild.get_channel
            places: Dict[int, bool] = {}

            def heard_by_everyone(channel_id: Any) -> bool:
                # Songs logged before the channels were recorded have none and are left out.
                if channel_id is None:
                    return False
                if channel_id not in places:
                    places[channel_id] = shareable(lookup(int(channel_id)))
                return places[channel_id]

            counts: Dict[str, List[Any]] = {}
            for video_id, title, requester_id, skipped, text_id, voice_id in rows:
                # Hidden members' requests are not counted; neither are songs played in a voice
                # channel, or shown in a text channel, that not everyone can see (or that is NSFW).
                if requester_id is not None and int(requester_id) in hidden:
                    continue
                if not (heard_by_everyone(voice_id) and (text_id == here_id or heard_by_everyone(text_id))):
                    continue
                entry = counts.setdefault(video_id, [title, 0, 0])
                entry[1] += 1
                entry[2] += int(skipped or 0)
            if not counts:
                return f"No songs were played for everyone on this server in the last {days} days."
            # Most plays first; rows come newest first, so ties go to the song played last.
            top = sorted(counts.items(), key=lambda item: -item[1][1])[:limit]
            lines = [
                f"{index}. {user_text(title or video_id)} — {plays} plays" + (f", skipped {skips}" if skips else "")
                for index, (video_id, (title, plays, skips)) in enumerate(top, 1)
            ]
            return f"Most played in the last {days} days:\n" + "\n".join(lines)

        return [
            StructuredTool.from_function(
                coroutine=get_popular_songs, metadata={"target_agent_mode": "info", "tool_group": "music"}
            )
        ]
