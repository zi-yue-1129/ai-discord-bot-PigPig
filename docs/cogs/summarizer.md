# File: `cogs/summarizer.py`

## Overview
The Summarizer cog provides AI-powered conversation summarization using LangChain agents. It allows users to summarize recent chat history in a Discord channel, extracting key themes, decisions, and action items while maintaining links back to the original messages.

## Classes

### `SummarizerCog`
Cog for conversation summarization using AI with source mapping and character limits.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `MAX_CHAR_COUNT` (`Any`): Instance attribute managing MAX_CHAR_COUNT.
  - `EMBED_DESC_LIMIT` (`Any`): Instance attribute managing EMBED_DESC_LIMIT.

- **Methods**:
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `summarize(interaction, limit, persona, only_me) -> None`: Analyze and summarize recent channel conversation history using an AI agent.

## Functions

### `setup(bot) -> Any`
Set up the SummarizerCog.

