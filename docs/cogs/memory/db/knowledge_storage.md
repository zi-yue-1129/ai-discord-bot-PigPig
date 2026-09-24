# File: `cogs/memory/db/knowledge_storage.py`

## Overview
KnowledgeStorage: handles guild and channel level knowledge storage.

## Classes

### `KnowledgeStorage`
Handles knowledge table storage operations.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: Initialize with a DatabaseConnection instance.
  - `get_knowledge(target_type: str, target_id: str) -> Optional[str]`: Retrieve knowledge for a specific scope (guild or channel).
  - `update_knowledge(target_type: str, target_id: str, content: str) -> bool`: Update or insert knowledge for a specific scope.
  - `delete_knowledge(target_type: str, target_id: str) -> bool`: Delete knowledge for a specific scope.

## Functions

No module-level functions defined in this file.
