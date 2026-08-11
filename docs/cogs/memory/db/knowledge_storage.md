# File: `cogs/memory/db/knowledge_storage.py`

## Overview
KnowledgeStorage: handles guild and channel level knowledge storage.

This module provides persistence for shared interaction knowledge, including
inside jokes, relationships, and special events.

## Classes

### `KnowledgeStorage`
Handles knowledge table storage operations.

- **Attributes**:
  - `db` (`Any`): Instance attribute managing db.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_knowledge(target_type, target_id) -> Optional[str]`: Retrieve knowledge for a specific scope (guild or channel).  Args:     target_type: Either 'guild' or 'channel'.     target_id: The Discord snowflake ID for the target.  Returns:     The stored knowledge content as a string, or None if not found.
  - `update_knowledge(target_type, target_id, content) -> bool`: Update or insert knowledge for a specific scope.  Args:     target_type: Either 'guild' or 'channel'.     target_id: The Discord snowflake ID for the target.     content: The new structured knowledge text.  Returns:     True if successful, False otherwise.
  - `delete_knowledge(target_type, target_id) -> bool`: Delete knowledge for a specific scope.  Args:     target_type: Either 'guild' or 'channel'.     target_id: The Discord snowflake ID for the target.  Returns:     True if something was deleted, False otherwise.
