# File: `cogs/summarizer.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `summarizer` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `SummarizerCog`
Cog for conversation summarization using AI with source mapping and character limits.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `MAX_CHAR_COUNT` (`Any`): Instance attribute for MAX_CHAR_COUNT.
  - `EMBED_DESC_LIMIT` (`Any`): Instance attribute for EMBED_DESC_LIMIT.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_split_text_robustly(text) -> Any`: Split long text into multiple chunks safely, handling exceptionally long single lines.
  - `summarize(interaction, limit, persona, only_me) -> None`: Analyze and summarize recent channel conversation history using an AI agent.

## Functions

### `setup(bot) -> Any`
Set up the SummarizerCog.
