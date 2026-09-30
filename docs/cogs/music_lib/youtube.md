# File: `cogs/music_lib/youtube.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/music_lib/youtube.py`.

## Classes

### `YouTubeManager`
Class representing YouTubeManager.

- **Attributes**:
  - `time_limit` (`Any`): Instance attribute time_limit
  - `settings` (`Any`): Instance attribute settings
  - `ffmpeg_config` (`Any`): Instance attribute ffmpeg_config

- **Methods**:
  - `_get_default_ffmpeg_config(self) -> dict`: Method _get_default_ffmpeg_config.
  - `_build_postprocessor_args(self) -> list`: Method _build_postprocessor_args.
  - `create(cls, time_limit) -> Any`: Method create.
  - `search_videos(self, query, max_results) -> Any`: Method search_videos.
  - `download_playlist(self, url, folder, interaction) -> tuple[Optional[List[Dict[str, Any]]], Optional[str]]`: Download a YouTube playlist.  Args:     url: The YouTube playlist URL.     folder: The destination folder path.     interaction: The Discord interaction object.  Returns:     A tuple of (video_infos, error_message).
  - `get_video_info_without_download(self, url, interaction) -> tuple[Optional[Dict[str, Any]], Optional[str]]`: Get video information without downloading.  Args:     url: The YouTube video URL.     interaction: The Discord interaction object.  Returns:     A tuple of (video_info, error_message).
  - `download_audio(self, url, folder, interaction) -> tuple[Optional[Dict[str, Any]], Optional[str]]`: Download audio from YouTube.  Args:     url: The YouTube video URL.     folder: The destination folder path.     interaction: The Discord interaction object.  Returns:     A tuple of (video_info, error_message).
  - `get_thumbnail_url(self, video_id) -> Any`: Method get_thumbnail_url.
  - `get_related_videos(self, video_id, title, author, interaction, limit, exclude_ids) -> tuple[List[Dict[str, Any]], Optional[str]]`: Get related videos for a YouTube video.  Args:     video_id: The YouTube video ID.     title: The title of the video.     author: The author/channel of the video.     interaction: The Discord interaction object.     limit: The maximum number of recommendations.     exclude_ids: A set of video IDs to exclude.  Returns:     A tuple of (related_videos, error_message).

## Functions

### `check_ffmpeg(ffmpeg_path) -> Any`
Function check_ffmpeg.

