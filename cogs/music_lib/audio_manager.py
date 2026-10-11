import os
import asyncio
from typing import Dict, Any, Optional
from addons.logging import get_logger
from discord import AudioSource, FFmpegPCMAudio, PCMVolumeTransformer

log = get_logger(source=__name__, server_id="system")


class AudioManager:
    def __init__(self):
        # Per-guild audio source tracking to avoid cross-guild interference.
        self._current_audio: Dict[int, Optional[FFmpegPCMAudio]] = {}

    def create_audio_source(self, song: Dict[str, Any], volume: float = 1.0) -> AudioSource:
        """Create an FFmpeg audio source based on song information.

        Args:
            song: The song entry (``file_path``, or ``stream_url`` for live streams).
            volume: Playback volume from 0.0 to 1.0.

        Returns:
            An audio source whose volume can be changed while it plays.

        Raises:
            ValueError: If the song has no playable file or stream URL.
        """
        is_live = song.get('is_live', False)

        if is_live:
            stream_url = song.get('stream_url')
            if not stream_url:
                raise ValueError("Live song is missing stream_url")
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
            }
            return PCMVolumeTransformer(FFmpegPCMAudio(stream_url, **ffmpeg_options), volume=volume)

        file_path = song.get('file_path')
        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"Audio file does not exist or invalid path: {file_path}")
        return PCMVolumeTransformer(FFmpegPCMAudio(file_path), volume=volume)

    async def delete_file(self, guild_id: int, file_path: str):
        """Non-blocking file deletion using asyncio.to_thread."""
        try:
            if os.path.exists(file_path):
                await asyncio.to_thread(os.remove, file_path)
                log.debug(f"[Music] Guild ID: {guild_id}, file deletion successful: {file_path}")
        except Exception as e:
            log.warning(f"[Music] Guild ID: {guild_id}, file deletion failed: {e}")

    async def cleanup_guild_files(self, guild_id: int, folder: str):
        """Clean up all audio files for a guild."""
        try:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                await self.delete_file(guild_id, file_path)
        except FileNotFoundError:
            pass
