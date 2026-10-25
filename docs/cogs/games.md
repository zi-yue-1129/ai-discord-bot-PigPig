# Games Cog Documentation

## Overview

The Games cog runs games for the whole channel: a quiz about the server and a word chain. The quiz about the server's own history: questions are written from the server's episodic memories (the conversation summaries the memory system keeps), so when the answer is revealed everyone can see where it came from and jump back to the original messages.

Points from every game go to `/leaderboard top kind:Game points`.

## `/game quiz [rounds] [days] [this_channel]`

| Option | Meaning |
|---|---|
| `rounds` | Number of questions, 3–10 (default 5) |
| `days` | Only use memories from the last this many days |
| `this_channel` | Only use memories from the channel the quiz runs in |

How a game goes:

1. The bot picks random memories of this server (`QdrantStore.sample_memories`, three per wanted question) and asks the model for one four-option question each.
2. A question is used only if the reply is valid JSON with four distinct options **and the correct option appears word for word in the memory**, so the model cannot make facts up. Memories whose authors all opted out with `/leaderboard optout` are never used, and neither are memories from channels `@everyone` cannot read (unless the quiz is played in that same channel), so a quiz never reveals what was said in a restricted channel.
3. Each question is posted with A–D buttons. Everyone has 20 seconds; only a player's first answer counts.
4. A correct answer scores 500 points plus up to 500 more the faster it came.
5. The answer is revealed with how many got it right, the **source** (channel, day, link to the original messages) and the standings.
6. After the last question the final standings are posted and the points are saved.

Only one game runs per channel at a time. The quiz needs the memory system (Qdrant) and a working model; otherwise it says so.

## `/game chain [homophones]`

A word chain in the channel. The bot posts the first word; each next word has to start with the last character of the one before.

- A move is any message that is a single word: 2–8 Chinese characters or kana, or 2–20 Latin letters. Other chatter in the channel is ignored, and the bot does not chat back to moves.
- Each move gets a reaction: ✅ accepted, ❌ wrong first character, 🔁 already used, ⏳ same player twice in a row, 🚫 ends in ん (nothing can follow it).
- Japanese small kana, the long-vowel mark and katakana/hiragana are folded (`コーヒー` continues with `ひ`). Latin words chain by letter.
- `homophones:True` also accepts a Chinese character with the same pinyin, tones ignored (needs the `pypinyin` package; without it the option says so and only the exact character counts).
- When nobody continues for 30 seconds, the bot plays one word (written by the model and checked against the rules). When nobody continues for 60 seconds after that, the game ends; it also ends after 15 minutes.
- Each accepted word is worth 10 points. The result shows the last words of the chain and who played the most.

## Storage

`game_scores` in `data/community.db`: `(guild_id, user_id, game, points, played_at)`.

## Code

- `cogs/games.py` — the cog, the answer buttons and the game loop
- `cogs/games_lib/quiz.py` — question validation, scoring
- `cogs/games_lib/chain.py` — word chain rules (normalising words, chaining, homophones)
- `bot.py` — hands messages in a running chain to `GamesCog.handle_message` before chat handling
- `llm/game_writer.py` — asks the model for a quiz question or the bot's word chain move
- `cogs/memory/vector_stores/qdrant_store.py` — `sample_memories` (Qdrant random sampling, filtered by guild, channel and time)
