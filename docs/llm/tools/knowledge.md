# File: `llm/tools/knowledge.py`

## Overview
The `KnowledgeTools` class provides tools for the LLM to manage shared context and cultural facts at the Guild (Server) and Channel levels. Unlike episodic memory (which is raw history), knowledge tools are used to store "distilled" information like inside jokes, relationship statuses, aliases, and channel-specific rules.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `knowledge.py`, providing vital integrations within the PigPig bot ecosystem.
Knowledge tools for managing guild and channel level memories.

This module provides tools for the LLM to store and update shared information
like inside jokes, relationships, aliases, and special events.

## Classes

### `UpdateKnowledgeInput`
Input for updating knowledge.

- **Attributes**:
  - `new_information` (`str`): Property holding the new_information state.
  - `category` (`str`): Property holding the category state.

### `UpdateGuildKnowledgeTool`
Tool to update knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Property holding the name state.
  - `description` (`str`): Property holding the description state.
  - `args_schema` (`Type[BaseModel]`): Property holding the args_schema state.
  - `runtime` (`Optional[Any]`): Property holding the runtime state.

- **Methods**:
  - `_run(new_information: str, category: str) -> str`: Synchronous run (not used).
  - `_arun(new_information: str, category: str) -> str`: Update guild-level knowledge.

### `UpdateChannelKnowledgeTool`
Tool to update knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Property holding the name state.
  - `description` (`str`): Property holding the description state.
  - `args_schema` (`Type[BaseModel]`): Property holding the args_schema state.
  - `runtime` (`Optional[Any]`): Property holding the runtime state.

- **Methods**:
  - `_run(new_information: str, category: str) -> str`: Synchronous run (not used).
  - `_arun(new_information: str, category: str) -> str`: Update channel-level knowledge.

### `ClearKnowledgeInput`
Input for clearing knowledge.

- **Attributes**:
  - `dummy` (`Optional[str]`): Property holding the dummy state.

### `ClearGuildKnowledgeTool`
Tool to clear all knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Property holding the name state.
  - `description` (`str`): Property holding the description state.
  - `args_schema` (`Type[BaseModel]`): Property holding the args_schema state.
  - `runtime` (`Optional[Any]`): Property holding the runtime state.

- **Methods**:
  - `_run(dummy: Optional[str]) -> str`: Synchronous run (not used).
  - `_arun(dummy: Optional[str]) -> str`: Clear guild-level knowledge.

### `ClearChannelKnowledgeTool`
Tool to clear knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Property holding the name state.
  - `description` (`str`): Property holding the description state.
  - `args_schema` (`Type[BaseModel]`): Property holding the args_schema state.
  - `runtime` (`Optional[Any]`): Property holding the runtime state.

- **Methods**:
  - `_run(dummy: Optional[str]) -> str`: Synchronous run (not used).
  - `_arun(dummy: Optional[str]) -> str`: Clear channel-level knowledge.

### `KnowledgeTools`
Wrapper class for discovering knowledge management tools.
Supported by the factory but get_tools() is preferred.

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: Any) -> None`: Performs internal processing logic.
  - `get_tools() -> list`: Return list of knowledge tools with shared runtime.

## Functions

### `get_tools(runtime: Any) -> list`
Discovery function for the tools factory.
