# File: `llm/tools/knowledge.py`

## Overview
Knowledge tools for managing guild and channel level memories.

This module provides tools for the LLM to store and update shared information
like inside jokes, relationships, aliases, and special events.

## Classes

### `UpdateKnowledgeInput`
Input for updating knowledge.

- **Attributes**:
  - `new_information` (`str`): Class attribute representing new_information.
  - `category` (`str`): Class attribute representing category.

### `UpdateGuildKnowledgeTool`
Tool to update knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `description` (`str`): Class attribute representing description.
  - `args_schema` (`Type[...]`): Class attribute representing args_schema.
  - `runtime` (`Optional[...]`): Class attribute representing runtime.

- **Methods**:
  - `_run(new_information, category) -> str`: Synchronous run (not used).
  - `_arun(new_information, category) -> str`: Update guild-level knowledge.

### `UpdateChannelKnowledgeTool`
Tool to update knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `description` (`str`): Class attribute representing description.
  - `args_schema` (`Type[...]`): Class attribute representing args_schema.
  - `runtime` (`Optional[...]`): Class attribute representing runtime.

- **Methods**:
  - `_run(new_information, category) -> str`: Synchronous run (not used).
  - `_arun(new_information, category) -> str`: Update channel-level knowledge.

### `ClearKnowledgeInput`
Input for clearing knowledge.

- **Attributes**:
  - `dummy` (`Optional[...]`): Class attribute representing dummy.

### `ClearGuildKnowledgeTool`
Tool to clear all knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `description` (`str`): Class attribute representing description.
  - `args_schema` (`Type[...]`): Class attribute representing args_schema.
  - `runtime` (`Optional[...]`): Class attribute representing runtime.

- **Methods**:
  - `_run(dummy) -> str`: Synchronous run (not used).
  - `_arun(dummy) -> str`: Clear guild-level knowledge.

### `ClearChannelKnowledgeTool`
Tool to clear knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `description` (`str`): Class attribute representing description.
  - `args_schema` (`Type[...]`): Class attribute representing args_schema.
  - `runtime` (`Optional[...]`): Class attribute representing runtime.

- **Methods**:
  - `_run(dummy) -> str`: Synchronous run (not used).
  - `_arun(dummy) -> str`: Clear channel-level knowledge.

### `KnowledgeTools`
Wrapper class for discovering knowledge management tools.
Supported by the factory but get_tools() is preferred.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.

- **Methods**:
  - `__init__(runtime) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get_tools() -> list`: Return list of knowledge tools with shared runtime.

## Functions

### `get_tools(runtime) -> list`
Discovery function for the tools factory.
