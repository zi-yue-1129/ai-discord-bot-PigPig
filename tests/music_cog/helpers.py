"""Fakes shared by the music cog tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional


# Downloaded songs point at real (empty) files: the player checks that a file exists before
# playing it and downloads the song again when it does not.
SONG_DIR = Path(tempfile.mkdtemp(prefix="music-test-songs-"))

BOT_USER_ID = 1
REQUESTER_ID = 42
GUILD_ID = 7


class FakeLangManager:
    """Returns the dotted translation path so tests can assert on message keys."""

    def translate(self, guild_id: str, *path: str, **kwargs: Any) -> str:
        return ".".join(path)


class FakeMessage:
    """A sent channel message that records deletion."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.deleted = False

    async def delete(self) -> None:
        self.deleted = True


class FakeChannel:
    """A text channel that records everything sent to it."""

    def __init__(self) -> None:
        self.sent: List[FakeMessage] = []

    async def send(self, **kwargs: Any) -> FakeMessage:
        message = FakeMessage(**kwargs)
        self.sent.append(message)
        return message


class FakeVoiceClient:
    """Voice client recording stop/pause calls."""

    def __init__(self, channel: object) -> None:
        self.channel = channel
        self.playing = False
        self.paused = False
        self.stop_calls = 0
        self.pause_calls = 0
        self.resume_calls = 0
        self.disconnected = False
        self.moved_to: Optional[object] = None
        self.sources: list = []

    def is_connected(self) -> bool:
        return True

    def is_playing(self) -> bool:
        return self.playing

    def is_paused(self) -> bool:
        return self.paused

    def play(self, source: Any) -> None:
        self.sources.append(source)
        self.playing = True

    def stop(self) -> None:
        self.stop_calls += 1
        self.playing = False

    async def move_to(self, channel: object) -> None:
        self.moved_to = channel
        self.channel = channel

    async def disconnect(self) -> None:
        self.disconnected = True

    def resume(self) -> None:
        self.resume_calls += 1
        self.paused = False
        self.playing = True

    def pause(self) -> None:
        self.pause_calls += 1
        self.paused = True
        self.playing = False


class FakeResponse:
    """Interaction response that records ephemeral replies."""

    def __init__(self) -> None:
        self.done = False
        self.sent: List[dict] = []

    def is_done(self) -> bool:
        return self.done

    async def send_message(self, *args: Any, **kwargs: Any) -> None:
        self.done = True
        self.sent.append({"args": args, **kwargs})

    async def defer(self, *args: Any, **kwargs: Any) -> None:
        self.done = True

    async def edit_message(self, *args: Any, **kwargs: Any) -> None:
        self.done = True
        self.sent.append({"args": args, "edited": True, **kwargs})


class FakeFollowup:
    """Interaction followup that records replies."""

    def __init__(self) -> None:
        self.sent: List[dict] = []

    async def send(self, *args: Any, **kwargs: Any) -> None:
        self.sent.append({"args": args, **kwargs})


class FakeControlView:
    """Player control view whose UI updates are no-ops."""

    current_embed = None

    async def update_embed(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def update_button_state(self, *args: Any, **kwargs: Any) -> None:
        return None

    def stop_progress_updater(self) -> None:
        return None


def make_member(user_id: int, voice_channel: Optional[object]) -> SimpleNamespace:
    """Builds a guild member standing in ``voice_channel`` (or in none)."""
    voice = None if voice_channel is None else SimpleNamespace(channel=voice_channel)
    return SimpleNamespace(
        id=user_id,
        name=f"user{user_id}",
        display_name=f"user{user_id}",
        voice=voice,
        display_avatar=SimpleNamespace(url="https://example.invalid/a.png"),
    )


def make_song(index: int, *, added_by: int = REQUESTER_ID) -> dict:
    """Builds a downloaded (ready to play) song entry whose file exists."""
    audio_file = SONG_DIR / f"song-{index}.mp3"
    audio_file.touch()
    return {
        "title": f"song {index}",
        "url": f"https://youtu.be/v{index}",
        "video_id": f"v{index}",
        "file_path": str(audio_file),
        "duration": 120,
        "author": "artist",
        "added_by": added_by,
    }


async def async_noop(*args: Any, **kwargs: Any) -> None:
    return None


def make_interaction(
    guild: SimpleNamespace, channel: FakeChannel, user: SimpleNamespace
) -> SimpleNamespace:
    """Builds a button interaction exposing recordable response/followup."""
    return SimpleNamespace(
        guild=guild,
        channel=channel,
        user=user,
        response=FakeResponse(),
        followup=FakeFollowup(),
    )


class EditableMessage(FakeMessage):
    """A channel message that also records edits."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.edits: List[dict] = []

    async def edit(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)


class EditableChannel:
    """A text channel whose sent messages can be edited (the player interface edits itself)."""

    def __init__(self) -> None:
        self.sent: List[EditableMessage] = []

    async def send(self, **kwargs: Any) -> EditableMessage:
        message = EditableMessage(**kwargs)
        self.sent.append(message)
        return message


class FakeThumbnails:
    """Stands in for the YouTube manager, which only supplies thumbnail URLs to the player embed."""

    def get_thumbnail_url(self, video_id: str) -> str:
        return f"https://example.invalid/{video_id}.jpg"


async def post_player(cog: Any, ctx: Any, index: int = 1) -> EditableMessage:
    """Posts the player interface for ``make_song(index)`` as the song that is playing."""
    song = make_song(index) | {"requester": ctx.user, "user_avatar": "https://example.invalid/a.png"}
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    return await cog.ui_manager.update_player_ui(ctx, song, None, FakeThumbnails(), cog)
