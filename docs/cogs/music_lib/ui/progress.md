# File: `cogs/music_lib/ui/progress.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/music_lib/ui/progress.py`.

## Classes

### `ProgressDisplay`
A class to handle the display of music playback progress

- **Attributes**:
  - None

- **Methods**:
  - `create_progress_bar(current, total, length) -> Any`: Create a more aesthetic progress bar  Args:     current (int): Current position in seconds     total (int): Total duration in seconds     length (int): Length of the progress bar      Returns:     str: Formatted progress bar with timestamps
  - `format_timestamp(seconds) -> Any`: Format seconds into MM:SS format  Args:     seconds (int): Time in seconds      Returns:     str: Formatted timestamp

## Functions

None
