# File: `cogs/music_lib/ui/progress.py`

## Overview
Core logic and functionalities for progress.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `ProgressDisplay`
A class to handle the display of music playback progress

- **Methods**:
  - `create_progress_bar(current, total, length) -> Any`: Create a more aesthetic progress bar  Args:     current (int): Current position in seconds     total (int): Total duration in seconds     length (int): Length of the progress bar      Returns:     str: Formatted progress bar with timestamps
  - `format_timestamp(seconds) -> Any`: Format seconds into MM:SS format  Args:     seconds (int): Time in seconds      Returns:     str: Formatted timestamp
