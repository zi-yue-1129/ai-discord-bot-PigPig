# File: `cogs/memory/db/knowledge_storage.py`

## Overview
KnowledgeStorage: handles guild and channel level knowledge storage.

This module provides persistence for shared interaction knowledge, including
inside jokes, relationships, and special events.

## Classes

### `KnowledgeStorage`
Handles knowledge table storage operations.

- **Attributes**:
  - `db` (`Any`): Instance attribute for db.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(db) -> None`: Initialize with a DatabaseConnection instance.
  - `get_knowledge(target_type, target_id) -> Optional[...]`: Retrieve knowledge for a specific scope (guild or channel).
  - `update_knowledge(target_type, target_id, content) -> bool`: Update or insert knowledge for a specific scope.
  - `delete_knowledge(target_type, target_id) -> bool`: Delete knowledge for a specific scope.
