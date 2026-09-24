# File: `cogs/music_lib/youtube.py`

## Overview
Core file handling responsibilities within the `cogs/music_lib` subsystem.

## Classes

### `YouTubeManager`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(time_limit) -> Any`: No description provided.
  - `_get_default_ffmpeg_config() -> dict`: No description provided.
  - `_build_postprocessor_args() -> list`: No description provided.
  - `create(cls, time_limit) -> Any`: No description provided.
  - `search_videos(query, max_results) -> Any`: No description provided.
  - `download_playlist(url: str, folder: str, interaction: discord.Interaction) -> tuple[Tuple[Optional[List[Dict[Tuple[str, Any]]]], Optional[str]]]`: Download a YouTube playlist.
  - `get_video_info_without_download(url: str, interaction: discord.Interaction) -> tuple[Tuple[Optional[Dict[Tuple[str, Any]]], Optional[str]]]`: Get video information without downloading.
  - `download_audio(url: str, folder: str, interaction: discord.Interaction) -> tuple[Tuple[Optional[Dict[Tuple[str, Any]]], Optional[str]]]`: Download audio from YouTube.
  - `get_thumbnail_url(video_id) -> Any`: No description provided.
  - `get_related_videos(video_id: str, title: str, author: str, interaction: discord.Interaction, limit: int, exclude_ids: Optional[Set[str]]) -> tuple[Tuple[List[Dict[Tuple[str, Any]]], Optional[str]]]`: Get related videos for a YouTube video.

## Functions

### `check_ffmpeg(ffmpeg_path) -> Any`
No description provided.

