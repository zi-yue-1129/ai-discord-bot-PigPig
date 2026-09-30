# File: `cogs/eat/views.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/eat/views.py`.

## Classes

### `DislikeModal`
Modal for users to provide feedback on disliked restaurants.

- **Attributes**:
  - `reason` (`Any`): Attribute reason
  - `db` (`Any`): Instance attribute db
  - `record_id` (`Any`): Instance attribute record_id
  - `detail_view` (`Any`): Instance attribute detail_view
  - `lang_manager` (`Any`): Instance attribute lang_manager
  - `guild_id` (`Any`): Instance attribute guild_id

- **Methods**:
  - `on_submit(self, interaction) -> Any`: Handle modal submission.

### `EatDetailView`
Interactive View after selecting a single restaurant.

- **Attributes**:
  - `result` (`Any`): Instance attribute result
  - `db` (`Any`): Instance attribute db
  - `record_id` (`Any`): Instance attribute record_id
  - `discord_id` (`Any`): Instance attribute discord_id
  - `provider` (`Any`): Instance attribute provider
  - `keyword` (`Any`): Instance attribute keyword
  - `browse_results` (`Any`): Instance attribute browse_results
  - `browse_index` (`Any`): Instance attribute browse_index
  - `lang_manager` (`Any`): Instance attribute lang_manager
  - `guild_id` (`Any`): Instance attribute guild_id
  - `_rated` (`Any`): Instance attribute _rated

- **Methods**:
  - `_update_labels(self) -> Any`: Update button labels based on localization.
  - `map_button(self, interaction, button) -> Any`: Provide a link to Google Maps for the selected restaurant.
  - `menu_button(self, interaction, button) -> Any`: Display a menu image if available.
  - `review_button(self, interaction, button) -> Any`: Generate food reviews using LangChain streaming.
  - `like_button(self, interaction, button) -> Any`: Record positive feedback for the restaurant.
  - `dislike_button(self, interaction, button) -> Any`: Record negative feedback and open a reason modal.
  - `back_button(self, interaction, button) -> Any`: Return to the multi-result browsing View.
  - `on_timeout(self) -> Any`: Disable all buttons when the View times out.

### `EatBrowseView`
Multi-result browsing View, supporting pagination and dropdown selection.

- **Attributes**:
  - `results` (`Any`): Instance attribute results
  - `keyword` (`Any`): Instance attribute keyword
  - `db` (`Any`): Instance attribute db
  - `discord_id` (`Any`): Instance attribute discord_id
  - `provider` (`Any`): Instance attribute provider
  - `current_index` (`Any`): Instance attribute current_index
  - `lang_manager` (`Any`): Instance attribute lang_manager
  - `guild_id` (`Any`): Instance attribute guild_id
  - `_max_viewed_index` (`Any`): Instance attribute _max_viewed_index
  - `_is_fetching` (`Any`): Instance attribute _is_fetching

- **Methods**:
  - `_update_labels(self) -> Any`: Update button labels based on localization.
  - `_background_prefetch(self) -> Any`: Complete detailed restaurant info in the background.
  - `_rebuild_select(self) -> Any`: Rebuild the dropdown selection menu.
  - `_select_callback(self, interaction) -> Any`: Handle restaurant selection from dropdown.
  - `_update_nav_buttons(self) -> Any`: Enable or disable navigation buttons based on current index.
  - `prev_button(self, interaction, button) -> Any`: Go to the previous restaurant result.
  - `next_button(self, interaction, button) -> Any`: Go to the next restaurant result.
  - `confirm_button(self, interaction, button) -> Any`: Confirm the current restaurant selection.
  - `regenerate_button(self, interaction, button) -> Any`: Cycle to the next recommended restaurant, performing real-time fetch if needed.
  - `on_timeout(self) -> Any`: Disable all buttons when the View times out.

## Functions

None
