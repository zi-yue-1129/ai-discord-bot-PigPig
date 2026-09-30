# File: `llm/tools/knowledge.py`

## Overview
Knowledge tools for managing guild and channel level memories.

This module provides tools for the LLM to store and update shared information
like inside jokes, relationships, aliases, and special events.

## Classes

### `UpdateKnowledgeInput`
Input for updating knowledge.

- **Attributes**:
  - `new_information` (`str`): Attribute new_information
  - `category` (`str`): Attribute category

- **Methods**:
  - None

### `UpdateGuildKnowledgeTool`
Tool to update knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Attribute name
  - `description` (`str`): Attribute description
  - `args_schema` (`Type[BaseModel]`): Attribute args_schema
  - `runtime` (`Optional[Any]`): Attribute runtime

- **Methods**:
  - `_run(self, new_information, category) -> str`: Synchronous run (not used).
  - `_arun(self, new_information, category) -> str`: Update guild-level knowledge.

### `UpdateChannelKnowledgeTool`
Tool to update knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Attribute name
  - `description` (`str`): Attribute description
  - `args_schema` (`Type[BaseModel]`): Attribute args_schema
  - `runtime` (`Optional[Any]`): Attribute runtime

- **Methods**:
  - `_run(self, new_information, category) -> str`: Synchronous run (not used).
  - `_arun(self, new_information, category) -> str`: Update channel-level knowledge.

### `ClearKnowledgeInput`
Input for clearing knowledge.

- **Attributes**:
  - `dummy` (`Optional[str]`): Attribute dummy

- **Methods**:
  - None

### `ClearGuildKnowledgeTool`
Tool to clear all knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Attribute name
  - `description` (`str`): Attribute description
  - `args_schema` (`Type[BaseModel]`): Attribute args_schema
  - `runtime` (`Optional[Any]`): Attribute runtime

- **Methods**:
  - `_run(self, dummy) -> str`: Synchronous run (not used).
  - `_arun(self, dummy) -> str`: Clear guild-level knowledge.

### `ClearChannelKnowledgeTool`
Tool to clear knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Attribute name
  - `description` (`str`): Attribute description
  - `args_schema` (`Type[BaseModel]`): Attribute args_schema
  - `runtime` (`Optional[Any]`): Attribute runtime

- **Methods**:
  - `_run(self, dummy) -> str`: Synchronous run (not used).
  - `_arun(self, dummy) -> str`: Clear channel-level knowledge.

### `KnowledgeTools`
Wrapper class for discovering knowledge management tools. Supported by the factory but get_tools() is preferred.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute runtime

- **Methods**:
  - `get_tools(self) -> list`: Return list of knowledge tools with shared runtime.

## Functions

### `get_tools(runtime) -> list`
Discovery function for the tools factory.

