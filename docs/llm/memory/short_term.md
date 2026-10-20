# Short-Term Memory Provider

## Overview

The `ShortTermMemoryProvider` is responsible for providing the immediate conversational context. It fetches the most recent messages from a Discord channel and converts them into a format that multimodal LLMs can understand.

## Core Logic

### 1. History Retrieval
- Fetches the last `N` messages (default 10) from the current channel.
- Orders them from oldest to newest to maintain conversational flow.

### 2. Message Conversion
Each Discord message is mapped to a LangChain `HumanMessage` or `AIMessage`.

### 3. Metadata Enrichment
To help the LLM understand the context better, the provider injects metadata into each message:
- **Speaker ID**: `[AuthorName | UserID:123 | MessageID:456]`
- **Timestamps**: Both Unix and human-readable UTC time.
- **Reactions**: Lists any emojis reacted to the message.
- **Replies**: If a message is a reply, it includes a summary of the referenced message (e.g., `Replying to @Author: 'Hello...'`).

### 4. Multimodal Support
The provider identifies and includes various attachment types:
- **Images**: Injected as `image_url` objects for vision-capable models (Gemini, GPT-4).
- **Videos/PDFs/Audio**: Injected as descriptive text placeholders (e.g., `[Video Attachment: filename.mp4]`).

## Multi-Agent Differentiation

The model only reliably sees the text of a message (most chat templates drop the `name` field), so the speaker is written into the prefix `[speaker | UserID:n | MessageID:n]`:
- **The bot's own messages**: the only `AIMessage` turns. The speaker is its plain username.
- **Everyone else, including other bots**: `HumanMessage` turns with `name` set to `AuthorName_UserID`.
  Treating another bot as an assistant turn would make the model take its words as its own.
- **Speaker label**: `Display Name (username)` when the display name differs from the username, so the name people use
  in conversation matches the history. Other bots are prefixed with `BOT `, for example `BOT MusicBot`.

The reply and info agent prompts (`base_configs/prompt/`) explain these rules to the model.

## Markers

Messages are wrapped in custom markers for easy parsing:
- `<som>`: Start of Message content.
- `<eom>`: End of Message content.

---
*Short-term memory provides the "now" of the conversation, ensuring the bot can follow threads, respond to replies, and "see" uploaded images.*