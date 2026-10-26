# Games Cog Documentation

## Overview

The Games cog runs games for the whole channel: a quiz about the server, a word chain, and guess the song. The quiz about the server's own history: questions are written from the server's episodic memories (the conversation summaries the memory system keeps), so when the answer is revealed everyone can see where it came from and jump back to the original messages.

Points from every game go to `/leaderboard top kind:Game points`.

## `/game quiz [rounds] [days] [this_channel]`

| Option | Meaning |
|---|---|
| `rounds` | Number of questions, 3–10 (default 5) |
| `days` | Only use memories from the last this many days |
| `this_channel` | Only use memories from the channel the quiz runs in |

How a game goes:

1. The bot picks random memories of this server (`QdrantStore.sample_memories`, three per wanted question) and asks the model for one four-option question each.
2. A question is used only if the reply is valid JSON with four distinct options **and the correct option appears word for word in the memory**, so the model cannot make facts up. Memories whose authors all opted out with `/leaderboard optout` are never used, and neither are memories from channels `@everyone` cannot read (unless the quiz is played in that same channel), so a quiz never reveals what was said in a restricted channel. Private threads count as restricted even under a public channel, and each question is checked again right before it is posted (a channel restricted or deleted meanwhile is skipped).
3. Each question is posted with A–D buttons. Everyone has 20 seconds; only a player's first answer counts.
4. A correct answer scores 500 points plus up to 500 more the faster it came.
5. The answer is revealed with how many got it right, the **source** (channel, day, link to the original messages) and the standings.
6. After the last question the final standings are posted and the points are saved.

Only one game runs per channel at a time, and a player can host one game at a time. Every model call a game makes counts as one use of the host's chat quota (the `chat` rate limit), fallback models included: each attempt at writing a quiz question and each attempt at the bot's word chain move. Starting a game costs nothing by itself. When the quota runs out, the quiz plays the questions it already has (or says the host hit the limit if it has none), and a word chain ends with a message. At most 3 model calls for games run at once across the bot; these limits live on the bot, so they survive a reload of the cog, and unloading the cog stops running games. Games can't be started in the music request channel. The quiz needs the memory system (Qdrant) and a working model; otherwise it says so.

## Asking the AI for a game

The AI's `start_server_game` tool (see [community tools](../llm/tools/community_tools.md)) does not start a game itself. It posts an offer with **Start** and **Cancel** buttons that only the member who asked can press; the offer pings nobody and expires after 2 minutes. A member has one open offer at a time (a new one replaces it) and a server at most 3. Pressing Start checks that the member may still read the channel (in a private thread: is in it), post and use commands there (a locked or archived thread needs Manage Threads) and runs the same checks as the slash command again and starts the game in the background with that member as host, charged to their quota like `/game`.

## `/game chain [homophones]`

A word chain in the channel. The bot posts the first word; each next word has to start with the last character of the one before.

- A move is any message that is a single word: 2–8 Chinese characters or kana, or 2–20 Latin letters. Other chatter in the channel is ignored, and the bot does not chat back to moves.
- Each move gets a reaction: ✅ accepted, ❌ wrong first character, 🔁 already used, ⏳ same player twice in a row, 🚫 ends in ん (nothing can follow it).
- Japanese small kana, the long-vowel mark and katakana/hiragana are folded (`コーヒー` continues with `ひ`). Latin words chain by letter.
- `homophones:True` also accepts a Chinese character with the same pinyin, tones ignored (needs the `pypinyin` package; without it the option says so and only the exact character counts).
- When nobody continues for 30 seconds, the bot plays one word (written by the model and checked against the rules). When nobody continues for 60 seconds after that, the game ends; it also ends after 15 minutes.
- Each accepted word is worth 10 points. The result shows the last words of the chain and who played the most.

## `/game guess_song [rounds]`

Short clips of songs this server listened to; the first player to type the song's name (or artist) in the text channel wins the round.

- You have to be in a voice channel, and no music may be playing, paused or queued. The bot joins your channel (or moves there if it is idle elsewhere) and leaves afterwards if it joined for the game.
- Songs come from the server's most played songs in `play_events` (needs at least 3). Each one is looked up again (`resolve_stream`); songs that can no longer be played are skipped.
- A clip plays for 15 seconds from a random point between 20% and 60% of the song (`-ss` seek). Guesses are taken for 30 seconds from the start of the clip.
- A guess counts when it is close (≥ 0.8 similarity) to a part of the YouTube title: the text around `-`/`|`/`/`, text inside 「」『』《》 or non-tag brackets, and each Chinese or Latin run of those. Tags such as "Official Music Video", "MV", "4K", "Lyrics" are ignored, and Traditional and Simplified Chinese compare alike (OpenCC).
- The winning guess gets ✅. Other messages in the channel during a round are not answered by the chat AI, except ones that mention the bot.
- The winner scores 500 points plus up to 500 more the faster they were. The answer shows the cleaned-up title with a link.
- Only one guess the song game runs per server (they share the voice connection). The game only stops its own clip: if someone starts music with `/play` during the game, the music keeps playing and the game stops; songs queued meanwhile start when it ends, and the bot stays in the channel for them.
- The clips are streamed from YouTube through yt-dlp, like `/play`, with no extra licensing filter: playing short clips of songs in a server is the bot owner's policy call.

## Storage

`game_scores` in `data/community.db`: `(guild_id, user_id, game, points, played_at)`.

## Code

- `cogs/games.py` — the cog, the answer buttons and the game loop
- `cogs/games_lib/quiz.py` — question validation, scoring
- `cogs/games_lib/chain.py` — word chain rules (normalising words, chaining, homophones)
- `cogs/games_lib/song_guess.py` — title parts, guess matching, clip start, points
- `bot.py` — hands messages in a running chain or song round to `GamesCog.handle_message` before chat handling
- `llm/game_writer.py` — asks the model for a quiz question or the bot's word chain move
- `cogs/memory/vector_stores/qdrant_store.py` — `sample_memories` (Qdrant random sampling, filtered by guild, channel and time)
