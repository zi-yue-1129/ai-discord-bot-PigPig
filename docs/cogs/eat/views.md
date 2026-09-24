# File: `cogs/eat/views.py`

## Overview
Core file handling responsibilities within the `cogs/eat` subsystem.

## Classes

### `DislikeModal`
Modal for users to provide feedback on disliked restaurants.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db: DB, record_id: int, detail_view: str, lang_manager, guild_id: str) -> Any`: No description provided.
  - `on_submit(interaction: discord.Interaction) -> Any`: Handle modal submission.

### `EatDetailView`
Interactive View after selecting a single restaurant.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(result: dict, db: DB, record_id: int, discord_id: str, provider, keyword: str, browse_results: list, browse_index: int, lang_manager, guild_id: str) -> Any`: No description provided.
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
  - None specified.

- **Methods**:
  - `__init__(results: list, keyword: str, db: DB, discord_id: str, provider, initial_index: int, lang_manager, guild_id: str) -> Any`: No description provided.
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

No module-level functions defined in this file.
