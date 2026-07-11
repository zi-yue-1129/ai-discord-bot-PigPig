# File: `addons/tokens.py`

## Overview
The `addons/tokens.py` module manages sensitive credentials and API keys. It serves as the single source of truth for all secrets required by the PigPig Bot.

This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `tokens.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `TOKENS`
Class managing TOKENS state and behavior.

- **Attributes**:
  - `token` (`Any`): Internal instance state.
  - `client_id` (`Any`): Internal instance state.
  - `client_secret_id` (`Any`): Internal instance state.
  - `secret_key` (`Any`): Internal instance state.
  - `bug_report_channel_id` (`Any`): Internal instance state.
  - `anthropic_api_key` (`Any`): Internal instance state.
  - `openai_api_key` (`Any`): Internal instance state.
  - `google_api_key` (`Any`): Internal instance state.
  - `tenor_api_key` (`Any`): Internal instance state.
  - `vector_store_api_key` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> None`: Performs internal processing logic.
  - `_validate_environment_variables() -> None`: Verify all required environment variables exist and are valid; terminate if validation fails.
