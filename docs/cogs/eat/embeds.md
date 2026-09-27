# File: `cogs/eat/embeds.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `embeds` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Functions

### `_rating_colour(rating) -> discord.Colour`
Return corresponding colour based on rating.

### `_price_label(price_level) -> str`
Convert price level (1-4) to $ symbols.

### `eatEmbed(keyword, title, address, rating, photo_url, price_level, opening_hours, lang_manager, guild_id) -> discord.Embed`
Detailed Embed after selecting a restaurant.

### `browseEmbed(results, current_index, lang_manager, guild_id) -> discord.Embed`
Multi-result browsing Embed, showing current restaurant info and pagination progress.

### `loadingEmbed(keyword, lang_manager, guild_id) -> discord.Embed`
Loading Embed for search in progress.

### `mapEmbed(map_url, lang_manager, guild_id) -> discord.Embed`
Embed for displaying restaurant map.

### `menuEmbed(menu_url, lang_manager, guild_id) -> discord.Embed`
Embed for displaying restaurant menu.
