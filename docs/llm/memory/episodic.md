# Episodic Memory Provider

## Overview

The `EpisodicMemoryProvider` implements a "long-term recall" mechanism. It uses semantic vector search to find past messages that are relevant to the user's current query, even if they occurred months ago.

## Core Logic

### 1. Query Pre-processing
- **Mention Removal**: Mentions (e.g., `<@123456>`) are stripped to prevent biased search results.
- **Short Message Skip**: Messages with fewer than 4 words are ignored to avoid searching for generic greetings like "hello" or "ok".

### 2. Vector Search
The provider interacts with the `vector_manager` (part of `cogs.memory`) to:
- Generate an embedding for the current message.
- Search the vector database for the top-k (default 3) most similar past messages in the current channel.

### 3. Formatting
Relevant fragments are formatted into a clear section for the LLM:
```text
--- Relevant Past Memories ---
[memory #1] User said: "I love pepperoni pizza" [[來源](jump_url)]
[memory #2] User said: "Pizza night on Friday?" [[來源](jump_url)]
--- End Past Memories ---
```
- **Source Linking**: Each memory fragment includes a Discord "Jump URL" and a relative timestamp (e.g., "3 months ago") using Discord's `<t:timestamp:R>` format.
- **Times are Discord timestamps only**: the prompt tells the bot to write every date and time as `<t:UNIX:STYLE>` (Discord shows each reader their own time zone and language), and the bot copies what it sees. A date written out as text (such as a UTC time) was copied into replies instead, so none is produced. The `search_episodic_memory` tool gives `Time: <t:S:F> - <t:E:t> (<t:S:R>)` and a ready-to-copy `Source: [[Source <t:S:R>](jump url)]` line; the injected blocks carry the same source label and the window (`(<t:S:F> - <t:E:t>)`) after the summary. Only a conversation whose start and end are the same second is given as one moment. The memory rules of the reply prompt name all three places and ask for the label to be copied.

### Recently Recalled Memories
The context of every message is built from scratch, so a fragment found for one message used to be gone at the next one, and a short follow-up ("when was that?") found nothing in the vector search. `RecentRecall` (`llm/memory/recent_recall.py`) keeps, per channel, the fragments that were injected or that `search_episodic_memory` returned, and `get()` tells them again as a `--- Recently Recalled Memories ---` block:
- **Scope**: strictly the same channel (a DM is its own channel); never across servers.
- **Lifetime**: `episodic_recent_ttl` seconds (default 600) after the last recall, at most `episodic_recent_max` (default 5) fragments per channel, newest first; in process memory only, a restart forgets them.
- **Privacy**: the opt-out list (`/leaderboard optout`) is read again every time; a fragment with a member who has hidden is dropped for good, and nothing is told while the list cannot be read.
- **Not twice**: only what was recalled *before* the message is told, and not what the message's own search already found.
- **Budget**: the block shares `max_chars` with the message's own memories (together never more); a fragment too long for what is left is skipped, not the shorter ones behind it. A search answered from the cache renews the fragments it tells.

## Performance Optimization

### TTL Caching
The provider maintains a thread-safe cache of recent search results:
- **Key**: `(channel_id, query_text)`
- **TTL**: 5 minutes (default).
- **Benefit**: Prevents redundant vector searches if the user repeats a query or if multiple agents need the same context.

### Async Execution
`EpisodicMemoryProvider.get()` is designed to run in parallel with other providers, ensuring that vector search latency does not block the entire bot response.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_k` | 3 | Number of fragments to retrieve. |
| `max_chars` | 1500 | Maximum total length of the context string. |
| `cache_ttl` | 300.0 | Seconds before a cache entry expires. |
| `recent_ttl` | 600.0 | Seconds a recalled fragment is told to the channel's next messages (`episodic_recent_ttl`). |
| `recent_max` | 5 | Recalled fragments kept per channel (`episodic_recent_max`). |

---
*This provider allows the bot to maintain a sense of history and "remember" facts that were never explicitly saved to procedural memory.*
