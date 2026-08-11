# File: `addons/tokens.py`

## Overview
The `addons/tokens.py` module manages sensitive credentials and API keys. It serves as the single source of truth for all secrets required by the PigPig Bot.

## Classes

### `TOKENS`
Manages the state and core operations for TOKENS.

- **Attributes**:
  - `token` (`Any`): Instance attribute managing token.
  - `client_id` (`Any`): Instance attribute managing client_id.
  - `client_secret_id` (`Any`): Instance attribute managing client_secret_id.
  - `secret_key` (`Any`): Instance attribute managing secret_key.
  - `bug_report_channel_id` (`Any`): Instance attribute managing bug_report_channel_id.
  - `anthropic_api_key` (`Any`): Instance attribute managing anthropic_api_key.
  - `openai_api_key` (`Any`): Instance attribute managing openai_api_key.
  - `google_api_key` (`Any`): Instance attribute managing google_api_key.
  - `tenor_api_key` (`Any`): Instance attribute managing tenor_api_key.
  - `vector_store_api_key` (`Any`): Instance attribute managing vector_store_api_key.

