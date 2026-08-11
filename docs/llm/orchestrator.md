# File: `llm/orchestrator.py`

## Overview
The `Orchestrator` class serves as the central coordinator for LLM-powered Discord interactions. It implements a sophisticated **Two-Phase Agent Architecture** to ensure high-quality, information-rich responses. It manages the entire lifecycle from capturing incoming Discord messages, gathering multi-layered context, executing information analysis, and finally generating a conversational reply.

## Classes

### `DirectToolOutputMiddleware`
Manages the state and core operations for DirectToolOutputMiddleware.

- **Methods**:
  - `after_tools(state, runtime) -> Any`: Executes logic for after_tools.

### `Orchestrator`
Orchestrator updated to accept ContextManager's new return type.

ContextManager.get_context now returns Tuple[str, List[BaseMessage]]:
  (procedural_context_str, short_term_msgs)

Short-term memory (short_term_msgs) is passed directly as LangChain
BaseMessage objects into agents' `messages` parameter to preserve
structure and avoid double-serialization.

- **Attributes**:
  - `model_manager` (`Any`): Instance attribute managing model_manager.
  - `bot` (`Any`): Instance attribute managing bot.
  - `context_manager` (`Any`): Instance attribute managing context_manager.

- **Methods**:
  - `handle_message(bot, message_edit, message, logger, announce_new_version) -> OrchestratorResponse`: Main entrypoint for handling an incoming Discord message.  This method adapts to ContextManager returning a tuple: (procedural_context_str, short_term_msgs).  short_term_msgs (List[BaseMessage]) are injected directly into the agents' messages lists (oldest -> newest), placed before the current user input to preserve conversation order.

