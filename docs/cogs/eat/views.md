# File: `cogs/eat/views.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `DislikeModal`
Modal for users to provide feedback on disliked restaurants.

- **Attributes**:
  - `db` (`Any`): Attribute holding db data.
  - `record_id` (`Any`): Attribute holding record_id data.
  - `detail_view` (`Any`): Attribute holding detail_view data.
  - `lang_manager` (`Any`): Attribute holding lang_manager data.
  - `guild_id` (`Any`): Attribute holding guild_id data.

- **Methods**:
  - `__init__(db: DB, record_id: int, detail_view: EatDetailView, lang_manager, guild_id: str) -> Any`: Executes __init__ logic.
  - `on_submit(interaction: discord.Interaction) -> Any`: Handle modal submission.

### `EatDetailView`
Interactive View after selecting a single restaurant.

- **Attributes**:
  - `result` (`Any`): Attribute holding result data.
  - `db` (`Any`): Attribute holding db data.
  - `record_id` (`Any`): Attribute holding record_id data.
  - `discord_id` (`Any`): Attribute holding discord_id data.
  - `provider` (`Any`): Attribute holding provider data.
  - `keyword` (`Any`): Attribute holding keyword data.
  - `browse_results` (`Any`): Attribute holding browse_results data.
  - `browse_index` (`Any`): Attribute holding browse_index data.
  - `lang_manager` (`Any`): Attribute holding lang_manager data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `_rated` (`Any`): Attribute holding _rated data.

- **Methods**:
  - `__init__(result: dict, db: DB, record_id: int, discord_id: str, provider, keyword: str, browse_results: list, browse_index: int, lang_manager, guild_id: str) -> Any`: Executes __init__ logic.
  - `_update_labels() -> Any`: Update button labels based on localization.
  - `map_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Provide a link to Google Maps for the selected restaurant.
  - `menu_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Display a menu image if available.
  - `review_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Generate food reviews using LangChain streaming.
  - `like_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Record positive feedback for the restaurant.
  - `dislike_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Record negative feedback and open a reason modal.
  - `back_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Return to the multi-result browsing View.
  - `on_timeout() -> Any`: Disable all buttons when the View times out.

### `EatBrowseView`
Multi-result browsing View, supporting pagination and dropdown selection.

- **Attributes**:
  - `results` (`Any`): Attribute holding results data.
  - `keyword` (`Any`): Attribute holding keyword data.
  - `db` (`Any`): Attribute holding db data.
  - `discord_id` (`Any`): Attribute holding discord_id data.
  - `provider` (`Any`): Attribute holding provider data.
  - `current_index` (`Any`): Attribute holding current_index data.
  - `lang_manager` (`Any`): Attribute holding lang_manager data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `_max_viewed_index` (`Any`): Attribute holding _max_viewed_index data.
  - `_is_fetching` (`Any`): Attribute holding _is_fetching data.

- **Methods**:
  - `__init__(results: list, keyword: str, db: DB, discord_id: str, provider, initial_index: int, lang_manager, guild_id: str) -> Any`: Executes __init__ logic.
  - `_update_labels() -> Any`: Update button labels based on localization.
  - `_background_prefetch() -> Any`: Complete detailed restaurant info in the background.
  - `_rebuild_select() -> Any`: Rebuild the dropdown selection menu.
  - `_select_callback(interaction: discord.Interaction) -> Any`: Handle restaurant selection from dropdown.
  - `_update_nav_buttons() -> Any`: Enable or disable navigation buttons based on current index.
  - `prev_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Go to the previous restaurant result.
  - `next_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Go to the next restaurant result.
  - `confirm_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Confirm the current restaurant selection.
  - `regenerate_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: Cycle to the next recommended restaurant, performing real-time fetch if needed.
  - `on_timeout() -> Any`: Disable all buttons when the View times out.

## Functions

No top-level functions defined.
