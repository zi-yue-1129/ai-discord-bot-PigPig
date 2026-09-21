# File: `cogs/eat/embeds.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

No classes defined.

## Functions

### `_rating_colour(rating: float) -> discord.Colour`
Return corresponding colour based on rating.

### `_price_label(price_level: int) -> str`
Convert price level (1-4) to $ symbols.

### `eatEmbed(keyword: str, title: str, address: str, rating, photo_url: str, price_level: int, opening_hours: list, lang_manager, guild_id: str) -> discord.Embed`
Detailed Embed after selecting a restaurant.

Supports both old (rating as string) and new (rating as float) formats.

### `browseEmbed(results: list, current_index: int, lang_manager, guild_id: str) -> discord.Embed`
Multi-result browsing Embed, showing current restaurant info and pagination progress.

### `loadingEmbed(keyword: str, lang_manager, guild_id: str) -> discord.Embed`
Loading Embed for search in progress.

### `mapEmbed(map_url: str, lang_manager, guild_id: str) -> discord.Embed`
Embed for displaying restaurant map.

### `menuEmbed(menu_url: str, lang_manager, guild_id: str) -> discord.Embed`
Embed for displaying restaurant menu.
