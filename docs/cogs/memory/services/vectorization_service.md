# File: `cogs/memory/services/vectorization_service.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `vectorization_service` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `VectorizationService`
Service responsible for converting EventSummary objects into MemoryFragment objects,
uploading them to the vector store.

Dependencies are injected to keep this service testable and decoupled:
  - bot: used only for contextual logging if needed
  - storage: implements StorageInterface
  - vector_manager: object that exposes .store.add_memories(...)
  - settings: MemoryConfig

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `storage` (`Any`): Instance attribute for storage.
  - `vector_manager` (`Any`): Instance attribute for vector_manager.
  - `settings` (`Any`): Instance attribute for settings.

- **Methods**:
  - `__init__(bot, storage, vector_manager, settings) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `process_event_summaries(event_summaries) -> None`: Process a list of EventSummary objects and store them in the vector database.
  - `_convert_event_summaries_to_fragments(event_summaries) -> List[...]`: Convert EventSummary objects to MemoryFragment objects.
