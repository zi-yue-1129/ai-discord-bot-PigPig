# File: `cogs/eat/embeds.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/eat/embeds.py`.

## Classes

None

## Functions

### `_rating_colour(rating) -> discord.Colour`
Return corresponding colour based on rating.

### `_price_label(price_level) -> str`
Convert price level (1-4) to $ symbols.

### `eatEmbed(keyword, title, address, rating, photo_url, price_level, opening_hours, lang_manager, guild_id) -> discord.Embed`
Detailed Embed after selecting a restaurant.  Supports both old (rating as string) and new (rating as float) formats.

### `browseEmbed(results, current_index, lang_manager, guild_id) -> discord.Embed`
Multi-result browsing Embed, showing current restaurant info and pagination progress.

### `loadingEmbed(keyword, lang_manager, guild_id) -> discord.Embed`
Loading Embed for search in progress.

### `mapEmbed(map_url, lang_manager, guild_id) -> discord.Embed`
Embed for displaying restaurant map.

### `menuEmbed(menu_url, lang_manager, guild_id) -> discord.Embed`
Embed for displaying restaurant menu.

