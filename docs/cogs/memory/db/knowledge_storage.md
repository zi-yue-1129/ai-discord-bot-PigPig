# File: `cogs/memory/db/knowledge_storage.py`

## Overview
KnowledgeStorage: handles guild and channel level knowledge storage.

This module provides persistence for shared interaction knowledge, including
inside jokes, relationships, and special events.

## Classes

### `KnowledgeStorage`
Handles knowledge table storage operations.

- **Attributes**:
  - `db` (`Any`): Attribute holding db data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: Initialize with a DatabaseConnection instance.
  - `get_knowledge(target_type: str, target_id: str) -> Optional[str]`: Retrieve knowledge for a specific scope (guild or channel).
  - `update_knowledge(target_type: str, target_id: str, content: str) -> bool`: Update or insert knowledge for a specific scope.
  - `delete_knowledge(target_type: str, target_id: str) -> bool`: Delete knowledge for a specific scope.

## Functions

No top-level functions defined.
