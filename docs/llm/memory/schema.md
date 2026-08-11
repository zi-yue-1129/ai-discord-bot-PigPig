# File: `llm/memory/schema.py`

## Overview
Core logic and functionalities for schema.py. This file is part of the llm subsystem and handles the primary operations for its respective domain.

## Classes

### `UserInfo`
Information about a single user used by procedural memory.

- **Attributes**:
  - `user_background` (`Optional[str]`): Stores data related to user_background.
  - `procedural_memory` (`Dict[Tuple[str, Any]]`): Stores data related to procedural_memory.
  - `last_updated` (`Optional[str]`): Stores data related to last_updated.

### `ProceduralMemory`
Holds procedural memory for multiple users keyed by user_id.

- **Attributes**:
  - `user_info` (`Dict[Tuple[str, UserInfo]]`): Stores data related to user_info.

### `ShortTermMemory`
Stores recent messages; each message is a mapping containing at least author_id, author, content, timestamp (numeric UNIX seconds as float).

- **Attributes**:
  - `messages` (`List[Dict[Tuple[str, Any]]]`): Stores data related to messages.

### `SystemContext`
Aggregated context used to build prompts for the LLM.

- **Attributes**:
  - `short_term_memory` (`ShortTermMemory`): Stores data related to short_term_memory.
  - `procedural_memory` (`ProceduralMemory`): Stores data related to procedural_memory.
  - `current_channel_name` (`str`): Stores data related to current_channel_name.
  - `timestamp` (`float`): Stores data related to timestamp.
