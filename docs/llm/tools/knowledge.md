# File: `llm/tools/knowledge.py`

## Overview
Knowledge tools for managing guild and channel level memories.

This module provides tools for the LLM to store and update shared information
like inside jokes, relationships, aliases, and special events.

## Classes

### `UpdateKnowledgeInput`
Input for updating knowledge.

- **Attributes**:
  - `new_information` (`str`): Stores data related to new_information.
  - `category` (`str`): Stores data related to category.

### `UpdateGuildKnowledgeTool`
Tool to update knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `description` (`str`): Stores data related to description.
  - `args_schema` (`Type[BaseModel]`): Stores data related to args_schema.
  - `runtime` (`Optional[Any]`): Stores data related to runtime.

### `UpdateChannelKnowledgeTool`
Tool to update knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `description` (`str`): Stores data related to description.
  - `args_schema` (`Type[BaseModel]`): Stores data related to args_schema.
  - `runtime` (`Optional[Any]`): Stores data related to runtime.

### `ClearKnowledgeInput`
Input for clearing knowledge.

- **Attributes**:
  - `dummy` (`Optional[str]`): Stores data related to dummy.

### `ClearGuildKnowledgeTool`
Tool to clear all knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `description` (`str`): Stores data related to description.
  - `args_schema` (`Type[BaseModel]`): Stores data related to args_schema.
  - `runtime` (`Optional[Any]`): Stores data related to runtime.

### `ClearChannelKnowledgeTool`
Tool to clear knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `description` (`str`): Stores data related to description.
  - `args_schema` (`Type[BaseModel]`): Stores data related to args_schema.
  - `runtime` (`Optional[Any]`): Stores data related to runtime.

### `KnowledgeTools`
Wrapper class for discovering knowledge management tools.
Supported by the factory but get_tools() is preferred.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute managing runtime.

- **Methods**:
  - `get_tools() -> list`: Return list of knowledge tools with shared runtime.

## Functions

### `get_tools(runtime) -> list`
Discovery function for the tools factory.

