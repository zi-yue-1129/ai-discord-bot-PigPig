# File: `llm/tools/knowledge.py`

## Overview
Knowledge tools for managing guild and channel level memories.

## Classes

### `UpdateKnowledgeInput`
Input for updating knowledge.

- **Attributes**:
  - `new_information` (`str`): Class attribute
  - `category` (`str`): Class attribute

- **Methods**:
  - None specified.

### `UpdateGuildKnowledgeTool`
Tool to update knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Class attribute
  - `description` (`str`): Class attribute
  - `args_schema` (`Type[BaseModel]`): Class attribute
  - `runtime` (`Optional[Any]`): Class attribute

- **Methods**:
  - `_run(new_information: str, category: str) -> str`: Synchronous run (not used).
  - `_arun(new_information: str, category: str) -> str`: Update guild-level knowledge.

### `UpdateChannelKnowledgeTool`
Tool to update knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Class attribute
  - `description` (`str`): Class attribute
  - `args_schema` (`Type[BaseModel]`): Class attribute
  - `runtime` (`Optional[Any]`): Class attribute

- **Methods**:
  - `_run(new_information: str, category: str) -> str`: Synchronous run (not used).
  - `_arun(new_information: str, category: str) -> str`: Update channel-level knowledge.

### `ClearKnowledgeInput`
Input for clearing knowledge.

- **Attributes**:
  - `dummy` (`Optional[str]`): Class attribute

- **Methods**:
  - None specified.

### `ClearGuildKnowledgeTool`
Tool to clear all knowledge shared across the entire server.

- **Attributes**:
  - `name` (`str`): Class attribute
  - `description` (`str`): Class attribute
  - `args_schema` (`Type[BaseModel]`): Class attribute
  - `runtime` (`Optional[Any]`): Class attribute

- **Methods**:
  - `_run(dummy: Optional[str]) -> str`: Synchronous run (not used).
  - `_arun(dummy: Optional[str]) -> str`: Clear guild-level knowledge.

### `ClearChannelKnowledgeTool`
Tool to clear knowledge specific to the current channel.

- **Attributes**:
  - `name` (`str`): Class attribute
  - `description` (`str`): Class attribute
  - `args_schema` (`Type[BaseModel]`): Class attribute
  - `runtime` (`Optional[Any]`): Class attribute

- **Methods**:
  - `_run(dummy: Optional[str]) -> str`: Synchronous run (not used).
  - `_arun(dummy: Optional[str]) -> str`: Clear channel-level knowledge.

### `KnowledgeTools`
Wrapper class for discovering knowledge management tools.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(runtime: Any) -> None`: No description provided.
  - `get_tools() -> list`: Return list of knowledge tools with shared runtime.

## Functions

### `get_tools(runtime: Any) -> list`
Discovery function for the tools factory.

