# File: `llm/memory/schema.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `schema` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `UserInfo`
Information about a single user used by procedural memory.

- **Attributes**:
  - `user_background` (`Optional[...]`): Class attribute representing user_background.
  - `procedural_memory` (`Dict[...]`): Class attribute representing procedural_memory.
  - `last_updated` (`Optional[...]`): Class attribute representing last_updated.

### `ProceduralMemory`
Holds procedural memory for multiple users keyed by user_id.

- **Attributes**:
  - `user_info` (`Dict[...]`): Class attribute representing user_info.

### `ShortTermMemory`
Stores recent messages; each message is a mapping containing at least author_id, author, content, timestamp (numeric UNIX seconds as float).

- **Attributes**:
  - `messages` (`List[...]`): Class attribute representing messages.

### `SystemContext`
Aggregated context used to build prompts for the LLM.

- **Attributes**:
  - `short_term_memory` (`ShortTermMemory`): Class attribute representing short_term_memory.
  - `procedural_memory` (`ProceduralMemory`): Class attribute representing procedural_memory.
  - `current_channel_name` (`str`): Class attribute representing current_channel_name.
  - `timestamp` (`float`): Class attribute representing timestamp.
