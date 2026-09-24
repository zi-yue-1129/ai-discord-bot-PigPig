# File: `cogs/summarizer.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `SummarizerCog`
Cog for conversation summarization using AI with source mapping and character limits.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: No description provided.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_split_text_robustly(text: str) -> Any`: Split long text into multiple chunks safely, handling exceptionally long single lines.
  - `summarize(interaction: discord.Interaction, limit: int, persona: Optional[str], only_me: bool) -> None`: Analyze and summarize recent channel conversation history using an AI agent.

## Functions

### `setup(bot: commands.Bot) -> Any`
Set up the SummarizerCog.

