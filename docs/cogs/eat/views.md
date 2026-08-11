# File: `cogs/eat/views.py`

## Overview
Core logic and functionalities for views.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `DislikeModal`
Modal for users to provide feedback on disliked restaurants.

- **Attributes**:
  - `db` (`Any`): Instance attribute managing db.
  - `record_id` (`Any`): Instance attribute managing record_id.
  - `detail_view` (`Any`): Instance attribute managing detail_view.
  - `lang_manager` (`Any`): Instance attribute managing lang_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.

- **Methods**:
  - `on_submit(interaction) -> Any`: Handle modal submission.

### `EatDetailView`
Interactive View after selecting a single restaurant.

- **Attributes**:
  - `result` (`Any`): Instance attribute managing result.
  - `db` (`Any`): Instance attribute managing db.
  - `record_id` (`Any`): Instance attribute managing record_id.
  - `discord_id` (`Any`): Instance attribute managing discord_id.
  - `provider` (`Any`): Instance attribute managing provider.
  - `keyword` (`Any`): Instance attribute managing keyword.
  - `browse_results` (`Any`): Instance attribute managing browse_results.
  - `browse_index` (`Any`): Instance attribute managing browse_index.
  - `lang_manager` (`Any`): Instance attribute managing lang_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `_rated` (`Any`): Instance attribute managing _rated.

- **Methods**:
  - `map_button(interaction, button) -> Any`: Provide a link to Google Maps for the selected restaurant.
  - `menu_button(interaction, button) -> Any`: Display a menu image if available.
  - `review_button(interaction, button) -> Any`: Generate food reviews using LangChain streaming.
  - `like_button(interaction, button) -> Any`: Record positive feedback for the restaurant.
  - `dislike_button(interaction, button) -> Any`: Record negative feedback and open a reason modal.
  - `back_button(interaction, button) -> Any`: Return to the multi-result browsing View.
  - `on_timeout() -> Any`: Disable all buttons when the View times out.

### `EatBrowseView`
Multi-result browsing View, supporting pagination and dropdown selection.

- **Attributes**:
  - `results` (`Any`): Instance attribute managing results.
  - `keyword` (`Any`): Instance attribute managing keyword.
  - `db` (`Any`): Instance attribute managing db.
  - `discord_id` (`Any`): Instance attribute managing discord_id.
  - `provider` (`Any`): Instance attribute managing provider.
  - `current_index` (`Any`): Instance attribute managing current_index.
  - `lang_manager` (`Any`): Instance attribute managing lang_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `_max_viewed_index` (`Any`): Instance attribute managing _max_viewed_index.
  - `_is_fetching` (`Any`): Instance attribute managing _is_fetching.

- **Methods**:
  - `prev_button(interaction, button) -> Any`: Go to the previous restaurant result.
  - `next_button(interaction, button) -> Any`: Go to the next restaurant result.
  - `confirm_button(interaction, button) -> Any`: Confirm the current restaurant selection.
  - `regenerate_button(interaction, button) -> Any`: Cycle to the next recommended restaurant, performing real-time fetch if needed.
  - `on_timeout() -> Any`: Disable all buttons when the View times out.
