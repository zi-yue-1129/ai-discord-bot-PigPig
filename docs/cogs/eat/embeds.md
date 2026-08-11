# File: `cogs/eat/embeds.py`

## Overview
Core logic and functionalities for embeds.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Functions

### `eatEmbed(keyword, title, address, rating, photo_url, price_level, opening_hours, lang_manager, guild_id) -> discord.Embed`
Detailed Embed after selecting a restaurant.

Supports both old (rating as string) and new (rating as float) formats.

### `browseEmbed(results, current_index, lang_manager, guild_id) -> discord.Embed`
Multi-result browsing Embed, showing current restaurant info and pagination progress.

### `loadingEmbed(keyword, lang_manager, guild_id) -> discord.Embed`
Loading Embed for search in progress.

### `mapEmbed(map_url, lang_manager, guild_id) -> discord.Embed`
Embed for displaying restaurant map.

### `menuEmbed(menu_url, lang_manager, guild_id) -> discord.Embed`
Embed for displaying restaurant menu.

