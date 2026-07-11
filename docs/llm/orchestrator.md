# File: `llm/orchestrator.py`

## Overview
The `Orchestrator` class serves as the central coordinator for LLM-powered Discord interactions. It implements a sophisticated **Two-Phase Agent Architecture** to ensure high-quality, information-rich responses. It manages the entire lifecycle from capturing incoming Discord messages, gathering multi-layered context, executing information analysis, and finally generating a conversational reply.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `orchestrator.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `DirectToolOutputMiddleware`
Class managing DirectToolOutputMiddleware state and behavior.

- **Methods**:
  - `after_tools(state: Any, runtime: Any) -> Any`: Performs internal processing logic.

### `Orchestrator`
Orchestrator updated to accept ContextManager's new return type.

ContextManager.get_context now returns Tuple[str, List[BaseMessage]]:
  (procedural_context_str, short_term_msgs)

Short-term memory (short_term_msgs) is passed directly as LangChain
BaseMessage objects into agents' `messages` parameter to preserve
structure and avoid double-serialization.

- **Attributes**:
  - `model_manager` (`Any`): Internal instance state.
  - `bot` (`Any`): Internal instance state.
  - `context_manager` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Initialize model manager and context manager.
  - `_build_info_agent_prompt(bot_id: int, message: Message) -> str`: Build system prompt for info_agent from settings with fallback.
  - `_get_info_agent_fallback_prompt(bot_id: int) -> str`: Performs internal processing logic.
  - `_build_message_agent_prompt(bot_id: int, message: Message) -> str`: Build system prompt for message_agent using ProtectedPromptManager.
  - `_build_action_tools_rules(tools: List[Any]) -> str`: Inject behavioral rules for message-mode action tools.
  - `_sanitize_messages_for_model(messages: List[BaseMessage], model_name: str, image_cache: Optional[MutableMapping[Tuple]]) -> List[BaseMessage]`: Sanitize messages for the specific model.
  - `handle_message(bot: Any, message_edit: Message, message: Message, logger: Any, announce_new_version: bool) -> OrchestratorResponse`: Main entrypoint for handling an incoming Discord message.
