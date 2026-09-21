# File: `llm/memory/schema.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `UserInfo`
Information about a single user used by procedural memory.

- **Attributes**:
  - `user_background` (`Optional[str]`): Attribute holding user_background data.
  - `procedural_memory` (`Dict[Tuple[str, Any]]`): Attribute holding procedural_memory data.
  - `last_updated` (`Optional[str]`): Attribute holding last_updated data.

- **Methods**:
  - None specified.

### `ProceduralMemory`
Holds procedural memory for multiple users keyed by user_id.

- **Attributes**:
  - `user_info` (`Dict[Tuple[str, UserInfo]]`): Attribute holding user_info data.

- **Methods**:
  - None specified.

### `ShortTermMemory`
Stores recent messages; each message is a mapping containing at least author_id, author, content, timestamp (numeric UNIX seconds as float).

- **Attributes**:
  - `messages` (`List[Dict[Tuple[str, Any]]]`): Attribute holding messages data.

- **Methods**:
  - None specified.

### `SystemContext`
Aggregated context used to build prompts for the LLM.

- **Attributes**:
  - `short_term_memory` (`ShortTermMemory`): Attribute holding short_term_memory data.
  - `procedural_memory` (`ProceduralMemory`): Attribute holding procedural_memory data.
  - `current_channel_name` (`str`): Attribute holding current_channel_name data.
  - `timestamp` (`float`): Attribute holding timestamp data.

- **Methods**:
  - None specified.

## Functions

No top-level functions defined.
