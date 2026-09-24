# File: `llm/orchestrator.py`

## Overview
Core file handling responsibilities within the `llm` subsystem.

## Classes

### `DirectToolOutputMiddleware`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `after_tools(state, runtime) -> Any`: No description provided.

### `Orchestrator`
Orchestrator updated to accept ContextManager's new return type.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Initialize model manager and context manager.
  - `_build_info_agent_prompt(bot_id: int, message: Message) -> str`: Build system prompt for info_agent from settings with fallback.
  - `_get_info_agent_fallback_prompt(bot_id: int) -> str`: No description provided.
  - `_build_message_agent_prompt(bot_id: int, message: Message) -> str`: Build system prompt for message_agent using ProtectedPromptManager.
  - `_build_action_tools_rules(tools: List[Any]) -> str`: Inject behavioral rules for message-mode action tools.
  - `_sanitize_messages_for_model(messages: List[BaseMessage], model_name: str, image_cache: Optional[MutableMapping[Tuple[str, dict[Tuple[str, Any]]]]]) -> List[BaseMessage]`: Sanitize messages for the specific model.
  - `handle_message(bot: Any, message_edit: Message, message: Message, logger: Any, announce_new_version: bool) -> OrchestratorResponse`: Main entrypoint for handling an incoming Discord message.

## Functions

No module-level functions defined in this file.

