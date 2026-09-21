# File: `cogs/music_lib/youtube.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `YouTubeManager`
Core class implementation.

- **Attributes**:
  - `time_limit` (`Any`): Attribute holding time_limit data.

- **Methods**:
  - `__init__(time_limit) -> Any`: Executes __init__ logic.
  - `_get_default_ffmpeg_config() -> dict`: Executes _get_default_ffmpeg_config logic.
  - `_build_postprocessor_args() -> list`: Executes _build_postprocessor_args logic.
  - `create(cls, time_limit) -> Any`: Executes create logic.
  - `search_videos(query, max_results) -> Any`: Executes search_videos logic.
  - `download_playlist(url: str, folder: str, interaction: discord.Interaction) -> tuple[Tuple[Optional[List[Dict[Tuple[str, Any]]]], Optional[str]]]`: Download a YouTube playlist.
  - `get_video_info_without_download(url: str, interaction: discord.Interaction) -> tuple[Tuple[Optional[Dict[Tuple[str, Any]]], Optional[str]]]`: Get video information without downloading.
  - `download_audio(url: str, folder: str, interaction: discord.Interaction) -> tuple[Tuple[Optional[Dict[Tuple[str, Any]]], Optional[str]]]`: Download audio from YouTube.
  - `get_thumbnail_url(video_id) -> Any`: Executes get_thumbnail_url logic.
  - `get_related_videos(video_id: str, title: str, author: str, interaction: discord.Interaction, limit: int, exclude_ids: Optional[Set[str]]) -> tuple[Tuple[List[Dict[Tuple[str, Any]]], Optional[str]]]`: Get related videos for a YouTube video.

## Functions

### `check_ffmpeg(ffmpeg_path) -> Any`
Performs check_ffmpeg operations.
