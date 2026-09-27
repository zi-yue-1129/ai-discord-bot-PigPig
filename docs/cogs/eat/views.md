# File: `cogs/eat/views.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `views` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `DislikeModal`
Modal for users to provide feedback on disliked restaurants.

- **Attributes**:
  - `reason` (`Any`): Class attribute representing reason.
  - `db` (`Any`): Instance attribute for db.
  - `record_id` (`Any`): Instance attribute for record_id.
  - `detail_view` (`Any`): Instance attribute for detail_view.
  - `lang_manager` (`Any`): Instance attribute for lang_manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.

- **Methods**:
  - `__init__(db, record_id, detail_view, lang_manager, guild_id) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `translate`.
  - `on_submit(interaction) -> Any`: Handle modal submission.

### `EatDetailView`
Interactive View after selecting a single restaurant.

- **Attributes**:
  - `result` (`Any`): Instance attribute for result.
  - `db` (`Any`): Instance attribute for db.
  - `record_id` (`Any`): Instance attribute for record_id.
  - `discord_id` (`Any`): Instance attribute for discord_id.
  - `provider` (`Any`): Instance attribute for provider.
  - `keyword` (`Any`): Instance attribute for keyword.
  - `browse_results` (`Any`): Instance attribute for browse_results.
  - `browse_index` (`Any`): Instance attribute for browse_index.
  - `lang_manager` (`Any`): Instance attribute for lang_manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `_rated` (`Any`): Instance attribute for _rated.

- **Methods**:
  - `__init__(result, db, record_id, discord_id, provider, keyword, browse_results, browse_index, lang_manager, guild_id) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `_update_labels`.
  - `_update_labels() -> Any`: Update button labels based on localization.
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
  - `results` (`Any`): Instance attribute for results.
  - `keyword` (`Any`): Instance attribute for keyword.
  - `db` (`Any`): Instance attribute for db.
  - `discord_id` (`Any`): Instance attribute for discord_id.
  - `provider` (`Any`): Instance attribute for provider.
  - `current_index` (`Any`): Instance attribute for current_index.
  - `lang_manager` (`Any`): Instance attribute for lang_manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `_max_viewed_index` (`Any`): Instance attribute for _max_viewed_index.
  - `_is_fetching` (`Any`): Instance attribute for _is_fetching.

- **Methods**:
  - `__init__(results, keyword, db, discord_id, provider, initial_index, lang_manager, guild_id) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `_update_labels`.
  - `_update_labels() -> Any`: Update button labels based on localization.
  - `_background_prefetch() -> Any`: Complete detailed restaurant info in the background.
  - `_rebuild_select() -> Any`: Rebuild the dropdown selection menu.
  - `_select_callback(interaction) -> Any`: Handle restaurant selection from dropdown.
  - `_update_nav_buttons() -> Any`: Enable or disable navigation buttons based on current index.
  - `prev_button(interaction, button) -> Any`: Go to the previous restaurant result.
  - `next_button(interaction, button) -> Any`: Go to the next restaurant result.
  - `confirm_button(interaction, button) -> Any`: Confirm the current restaurant selection.
  - `regenerate_button(interaction, button) -> Any`: Cycle to the next recommended restaurant, performing real-time fetch if needed.
  - `on_timeout() -> Any`: Disable all buttons when the View times out.
