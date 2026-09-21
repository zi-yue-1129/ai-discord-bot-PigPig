# File: `llm/tools/knowledge.py`

## Overview
Knowledge tools for managing guild and channel level memories.

This module provides tools for the LLM to store and update shared information
like inside jokes, relationships, aliases, and special events.

## Classes

### `UpdateKnowledgeInput`
Input for updating knowledge.

- **Attributes**:
  - `new_information` (`str`): Attribute holding new_information data.
  - `category` (`str`): Attribute holding category data.

- **Methods**:
  - None specified.

### `UpdateGuildKnowledgeTool`
Tool to update knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `description` (`str`): Attribute holding description data.
  - `args_schema` (`Type[BaseModel]`): Attribute holding args_schema data.
  - `runtime` (`Optional[Any]`): Attribute holding runtime data.

- **Methods**:
  - `_run(new_information: str, category: str) -> str`: Synchronous run (not used).
  - `_arun(new_information: str, category: str) -> str`: Update guild-level knowledge.

### `UpdateChannelKnowledgeTool`
Tool to update knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `description` (`str`): Attribute holding description data.
  - `args_schema` (`Type[BaseModel]`): Attribute holding args_schema data.
  - `runtime` (`Optional[Any]`): Attribute holding runtime data.

- **Methods**:
  - `_run(new_information: str, category: str) -> str`: Synchronous run (not used).
  - `_arun(new_information: str, category: str) -> str`: Update channel-level knowledge.

### `ClearKnowledgeInput`
Input for clearing knowledge.

- **Attributes**:
  - `dummy` (`Optional[str]`): Attribute holding dummy data.

- **Methods**:
  - None specified.

### `ClearGuildKnowledgeTool`
Tool to clear all knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `description` (`str`): Attribute holding description data.
  - `args_schema` (`Type[BaseModel]`): Attribute holding args_schema data.
  - `runtime` (`Optional[Any]`): Attribute holding runtime data.

- **Methods**:
  - `_run(dummy: Optional[str]) -> str`: Synchronous run (not used).
  - `_arun(dummy: Optional[str]) -> str`: Clear guild-level knowledge.

### `ClearChannelKnowledgeTool`
Tool to clear knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `description` (`str`): Attribute holding description data.
  - `args_schema` (`Type[BaseModel]`): Attribute holding args_schema data.
  - `runtime` (`Optional[Any]`): Attribute holding runtime data.

- **Methods**:
  - `_run(dummy: Optional[str]) -> str`: Synchronous run (not used).
  - `_arun(dummy: Optional[str]) -> str`: Clear channel-level knowledge.

### `KnowledgeTools`
Wrapper class for discovering knowledge management tools.
Supported by the factory but get_tools() is preferred.

- **Attributes**:
  - `runtime` (`Any`): Attribute holding runtime data.

- **Methods**:
  - `__init__(runtime: Any) -> None`: Executes __init__ logic.
  - `get_tools() -> list`: Return list of knowledge tools with shared runtime.

## Functions

### `get_tools(runtime: Any) -> list`
Discovery function for the tools factory.
