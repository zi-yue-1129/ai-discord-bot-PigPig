# File: `llm/memory/schema.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/memory/schema.py`.

## Classes

### `UserInfo`
Information about a single user used by procedural memory.

- **Attributes**:
  - `user_background` (`Optional[str]`): Attribute user_background
  - `procedural_memory` (`Dict[str, Any]`): Attribute procedural_memory
  - `last_updated` (`Optional[str]`): Attribute last_updated

- **Methods**:
  - None

### `ProceduralMemory`
Holds procedural memory for multiple users keyed by user_id.

- **Attributes**:
  - `user_info` (`Dict[str, UserInfo]`): Attribute user_info

- **Methods**:
  - None

### `ShortTermMemory`
Stores recent messages; each message is a mapping containing at least author_id, author, content, timestamp (numeric UNIX seconds as float).

- **Attributes**:
  - `messages` (`List[Dict[str, Any]]`): Attribute messages

- **Methods**:
  - None

### `SystemContext`
Aggregated context used to build prompts for the LLM.

- **Attributes**:
  - `short_term_memory` (`ShortTermMemory`): Attribute short_term_memory
  - `procedural_memory` (`ProceduralMemory`): Attribute procedural_memory
  - `current_channel_name` (`str`): Attribute current_channel_name
  - `timestamp` (`float`): Attribute timestamp

- **Methods**:
  - None

## Functions

None
