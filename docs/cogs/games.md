# Games Cog Documentation

## Overview

The Games cog runs games for the whole channel. The first one is a quiz about the server's own history: questions are written from the server's episodic memories (the conversation summaries the memory system keeps), so when the answer is revealed everyone can see where it came from and jump back to the original messages.

Points from every game go to `/leaderboard top kind:Game points`.

## `/game quiz [rounds] [days] [this_channel]`

| Option | Meaning |
|---|---|
| `rounds` | Number of questions, 3–10 (default 5) |
| `days` | Only use memories from the last this many days |
| `this_channel` | Only use memories from the channel the quiz runs in |

How a game goes:

1. The bot picks random memories of this server (`QdrantStore.sample_memories`, three per wanted question) and asks the model for one four-option question each.
2. A question is used only if the reply is valid JSON with four distinct options **and the correct option appears word for word in the memory**, so the model cannot make facts up. Memories whose authors all opted out with `/leaderboard optout` are never used.
3. Each question is posted with A–D buttons. Everyone has 20 seconds; only a player's first answer counts.
4. A correct answer scores 500 points plus up to 500 more the faster it came.
5. The answer is revealed with how many got it right, the **source** (channel, day, link to the original messages) and the standings.
6. After the last question the final standings are posted and the points are saved.

Only one game runs per channel at a time. The quiz needs the memory system (Qdrant) and a working model; otherwise it says so.

## Storage

`game_scores` in `data/community.db`: `(guild_id, user_id, game, points, played_at)`.

## Code

- `cogs/games.py` — the cog, the answer buttons and the game loop
- `cogs/games_lib/quiz.py` — question validation, scoring
- `llm/quiz_writer.py` — asks the model for one question
- `cogs/memory/vector_stores/qdrant_store.py` — `sample_memories` (Qdrant random sampling, filtered by guild, channel and time)
