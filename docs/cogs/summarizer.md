# File: `cogs/summarizer.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `SummarizerCog`
Cog for conversation summarization using AI with source mapping and character limits.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `MAX_CHAR_COUNT` (`Any`): Attribute holding MAX_CHAR_COUNT data.
  - `EMBED_DESC_LIMIT` (`Any`): Attribute holding EMBED_DESC_LIMIT data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_split_text_robustly(text: str) -> Any`: Split long text into multiple chunks safely, handling exceptionally long single lines.
  - `summarize(interaction: discord.Interaction, limit: int, persona: Optional[str], only_me: bool) -> None`: Analyze and summarize recent channel conversation history using an AI agent.

## Functions

### `setup(bot: commands.Bot) -> Any`
Set up the SummarizerCog.
