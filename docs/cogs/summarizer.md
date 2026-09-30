# File: `cogs/summarizer.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/summarizer.py`.

## Classes

### `SummarizerCog`
Cog for conversation summarization using AI with source mapping and character limits.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `MAX_CHAR_COUNT` (`Any`): Instance attribute MAX_CHAR_COUNT
  - `EMBED_DESC_LIMIT` (`Any`): Instance attribute EMBED_DESC_LIMIT
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager

- **Methods**:
  - `cog_load(self) -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_split_text_robustly(self, text) -> Any`: Split long text into multiple chunks safely, handling exceptionally long single lines.
  - `summarize(self, interaction, limit, persona, only_me) -> None`: Analyze and summarize recent channel conversation history using an AI agent.

## Functions

### `setup(bot) -> Any`
Set up the SummarizerCog.

