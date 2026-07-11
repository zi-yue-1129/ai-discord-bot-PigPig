# File: `cogs/summarizer.py`

## Overview
The Summarizer cog provides AI-powered conversation summarization using LangChain agents. It allows users to summarize recent chat history in a Discord channel, extracting key themes, decisions, and action items while maintaining links back to the original messages.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `summarizer.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `SummarizerCog`
Cog for conversation summarization using AI with source mapping and character limits.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `MAX_CHAR_COUNT` (`Any`): Internal instance state.
  - `EMBED_DESC_LIMIT` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_split_text_robustly(text: str) -> Any`: Split long text into multiple chunks safely, handling exceptionally long single lines.
  - `summarize(interaction: discord.Interaction, limit: int, persona: Optional[str], only_me: bool) -> None`: Analyze and summarize recent channel conversation history using an AI agent.

## Functions

### `setup(bot: commands.Bot) -> Any`
Set up the SummarizerCog.
