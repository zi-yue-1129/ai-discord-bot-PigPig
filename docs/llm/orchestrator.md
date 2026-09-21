# File: `llm/orchestrator.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `DirectToolOutputMiddleware`
Core class implementation.

- **Attributes**:
  - None specified.

- **Methods**:
  - `after_tools(state, runtime) -> Any`: Executes after_tools logic.

### `Orchestrator`
Orchestrator updated to accept ContextManager's new return type.

ContextManager.get_context now returns Tuple[str, List[BaseMessage]]:
  (procedural_context_str, short_term_msgs)

Short-term memory (short_term_msgs) is passed directly as LangChain
BaseMessage objects into agents' `messages` parameter to preserve
structure and avoid double-serialization.

- **Attributes**:
  - `model_manager` (`Any`): Attribute holding model_manager data.
  - `bot` (`Any`): Attribute holding bot data.
  - `context_manager` (`Any`): Attribute holding context_manager data.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Initialize model manager and context manager.
  - `_build_info_agent_prompt(bot_id: int, message: Message) -> str`: Build system prompt for info_agent from settings with fallback.
  - `_get_info_agent_fallback_prompt(bot_id: int) -> str`: Executes _get_info_agent_fallback_prompt logic.
  - `_build_message_agent_prompt(bot_id: int, message: Message) -> str`: Build system prompt for message_agent using ProtectedPromptManager.
  - `_build_action_tools_rules(tools: List[Any]) -> str`: Inject behavioral rules for message-mode action tools.
  - `_sanitize_messages_for_model(messages: List[BaseMessage], model_name: str, image_cache: Optional[MutableMapping[Tuple[str, dict[Tuple[str, Any]]]]]) -> List[BaseMessage]`: Sanitize messages for the specific model.
  - `handle_message(bot: Any, message_edit: Message, message: Message, logger: Any, announce_new_version: bool) -> OrchestratorResponse`: Main entrypoint for handling an incoming Discord message.

## Functions

No top-level functions defined.
