"""Music player status for the AI's conversation context.

The reply agent calls the model once and never sees tool results, and the info
agent stops after one tool round, so the model cannot look the player up when it
needs to. The status is therefore placed into the context before the agents run.
"""

from typing import Any, Dict, List

from addons.settings import MusicAISettings


def format_seconds(seconds: Any) -> str:
    """Formats a duration in seconds as ``MM:SS`` (``??:??`` when unknown)."""
    try:
        minutes, secs = divmod(int(seconds), 60)
    except (TypeError, ValueError):
        return "??:??"
    return f"{minutes:02d}:{secs:02d}"


def render_music_context(status: Dict[str, Any], *, list_titles: bool, max_titles: int) -> str:
    """Renders the player status as plain text for the model.

    Args:
        status: The dict returned by ``MusicService.status``.
        list_titles: Whether to list the upcoming songs by title.
        max_titles: How many upcoming titles to list at most.

    Returns:
        A multi-line description of the player.
    """
    lines: List[str] = ["[Music Player]", f"State: {status['state']}"]
    current = status["current"]
    if current:
        lines.append(f"Now playing: '{current['title']}' by {current['author']} ({format_seconds(current['duration'])})")

    queue: List[Dict[str, Any]] = status["queue"]
    if not queue:
        lines.append("The queue is empty.")
    elif not list_titles:
        lines.append(f"Up next: {len(queue)} songs in the queue")
    else:
        lines.append(f"Up next ({len(queue)} songs):")
        for position, song in enumerate(queue[:max_titles], 1):
            lines.append(f"{position}. '{song['title']}' ({format_seconds(song['duration'])})")
        if len(queue) > max_titles:
            lines.append(f"... and {len(queue) - max_titles} more")

    lines.append(
        f"Loop mode: {status['mode']}; shuffle: {'on' if status['shuffle'] else 'off'}; "
        f"autoplay: {'on' if status['autoplay'] else 'off'}; volume: {status['volume']}%"
    )
    return "\n".join(lines)


async def build_music_context(bot: Any, guild: Any, settings: MusicAISettings) -> str:
    """Builds the music section of a conversation's context.

    Args:
        bot: The Discord bot (used to find the music cog).
        guild: The guild the message came from, or ``None`` in direct messages.
        settings: The AI-related music settings.

    Returns:
        The rendered status, or an empty string when the feature is disabled,
        the music cog is missing, or nothing is going on in this guild.
    """
    if not settings.status_in_context or guild is None:
        return ""
    cog = bot.get_cog("YTMusic")
    if cog is None:
        return ""
    status = cog.service.status(guild.id)
    nothing_going_on = status["state"] == "disconnected" or (
        status["state"] == "idle" and not status["current"] and not status["queue"]
    )
    if nothing_going_on:
        return ""
    return render_music_context(
        status, list_titles=settings.list_queue_titles, max_titles=settings.max_queue_titles
    )
