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

    def create_audio_source(self, song: Dict[str, Any], volume: float = 1.0, start_offset: float = 0.0,
                            audio_filter: Optional[str] = None) -> AudioSource:
        """Create an FFmpeg audio source based on song information.

        A local file is preferred. A song that is still downloading (or a live stream)
        is played from its stream URL.

        Args:
            song: The song entry (``file_path`` and/or ``stream_url``).
            volume: Playback volume from 0.0 to 1.0.
            start_offset: Seconds to skip at the start of the song (used to resume and seek);
                ignored for a live stream.
            audio_filter: An FFmpeg ``-af`` filter chain (see filters.py), or ``None``.

        Returns:
            An audio source whose volume can be changed while it plays.

        Raises:
            ValueError: If the song has neither a playable file nor a stream URL.
        """
        output_options = '-vn' + (f' -af "{audio_filter}"' if audio_filter else '')
        seek = f"-ss {start_offset:g} " if start_offset > 0 and not song.get('is_live') else ""
        file_path = song.get('file_path')
        if file_path and os.path.exists(file_path):
            options: Dict[str, Any] = {'options': output_options}
            if seek:
                options['before_options'] = seek.strip()
            return PCMVolumeTransformer(FFmpegPCMAudio(file_path, **options), volume=volume)

        stream_url = song.get('stream_url')
        if not stream_url:
            if song.get('is_live'):
                raise ValueError("Live song is missing stream_url")
            raise ValueError(f"Song has neither a local file nor a stream URL: {file_path}")

        before_options = seek + '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        headers = song.get('stream_headers')
        if headers:
            header_block = "".join(f"{name}: {value}\r\n" for name, value in headers.items())
            before_options += f' -headers "{header_block}"'
        ffmpeg_options = {'before_options': before_options, 'options': output_options}
        return PCMVolumeTransformer(FFmpegPCMAudio(stream_url, **ffmpeg_options), volume=volume)

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
