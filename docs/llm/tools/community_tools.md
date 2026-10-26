# Community Tools

`llm/tools/community_tools.py` lets the AI answer questions about the community features: rankings, achievements, the weekly recap, birthdays and events. `llm/tools/activity_tools.py` adds starting a game, who is playing what, and the most played songs.

The AI's answer is posted for everyone in the channel, so each tool returns only what a public post would show:

- Members who hid themselves with `/leaderboard optout` are never named, and what they did is not counted (recap numbers, event sign-ups). A hidden member asking about themselves is pointed to the private slash command. The opt-out list is read with `user_stats.hidden_member_ids()`; when it cannot be read, the leaderboard and recap answer "not available", the birthday tool answers "not available" and events are listed without counts. Tools never create a missing community database before the list was read.
- Text from a channel (channel names, quotes, words, event titles) is only used when the channel is *shareable*: every member can read it (`audience_can_read`) and it is not age-restricted (NSFW, its own or its parent's). An event in the channel the answer goes to is always listed.
- Names and other text members wrote go through `user_text()`: angle brackets are replaced, `@everyone`/`@here` are broken up, links become `[link]`, the text is cut to 100 characters and wrapped in `<<< >>>` so the model reads it as data.
- Nothing here calls a model or uses anyone's chat quota.

| Tool | Group | Loaded when | Arguments | Returns |
| --- | --- | --- | --- | --- |
| `get_leaderboard` | community | LeaderboardCog is loaded | `kind`: messages, streak or games; `period`: week, month or all | The top 10, as `/leaderboard top`, and the asker's own place |
| `get_achievements` | community | LeaderboardCog is loaded | `user_id` (defaults to the asker) | Unlocked achievements with dates, locked ones with what they need |
| `hide_my_stats` | core | LeaderboardCog is loaded | none | Hides the asker only. Showing oneself again is only possible with `/leaderboard optout hide:False`, so text that tricks the model cannot undo someone's choice |
| `get_server_recap` | community | CommunityCog is loaded | `period`: this_week or last_week | The weekly recap's facts (messages, shareable channels, talkers, words, quote, titles; no music) |
| `get_upcoming_birthdays` | community | CommunityCog is loaded (says so when birthdays are off for the server; building the tool list reads no database) | `days`: 1 to 30 | Saved birthdays, soonest first, without hidden members, bots or leavers |
| `list_upcoming_events` | events | EventsCog is loaded | none | Up to 10 events: number, title, Discord start timestamp, sign-up counts (without hidden members and people who left), link |
| `start_server_game` | games | GamesCog is loaded | `game`: quiz, chain or guess_song; `rounds`; `homophones`; `days`; `this_channel` | Posts an offer with Start and Cancel buttons only the asker can press; the game starts on Start, with the asker as host (same checks, again on the press, and quota as `/game`) |
| `who_is_playing` | playing | PlayingCog is loaded (says so when `/community playing` is off) | none | Games being played now, most players first, naming and counting only players who can read the channel (in a private thread: its members) and are not hidden |
| `get_popular_songs` | music | the music player's play log exists | `period`: week or month; `limit` | The most played songs and their play and skip counts, counted only where everyone could hear them |

### Starting a game

The model never starts a game by itself: `start_server_game` posts an offer that pings nobody, and only the asker can press Start (others are told it is not theirs). Text that tricks the model can at most post an offer. An offer expires after 2 minutes; a host has one open offer (a new one replaces it) and a server at most 3. Pressing Start looks the asker up again and runs the `/game` checks again: they must still be allowed to see the channel, post in it and use commands there, and the channel, the host or the music may be busy by then. A game cancelled before it ran (the cog unloaded) frees the channel and the host, and a press still being handled when the cog unloads starts nothing. Guess the song reads its song pool on a worker thread.

### Popular songs

The play log records the player's text channel and the voice channel of each play. A play is counted only when the voice channel is shareable and `@everyone` may connect to it (no overwrite denying Connect), and the text channel is shareable or is the channel the answer goes to, and not when a hidden member asked for it. Plays logged before the channels were recorded are not counted. The opt-out list, the play log and the server settings are read on worker threads without the stores' locks (`CommunityStore.read_settings`, `TasteStore._reader`), so a locked or slow database cannot stall the bot; the opt-out list is read last, so someone who hides while the tool reads is left out. The play log is in WAL mode and chart reads do not take its lock, so a slow read never holds up the player's writes. `/game guess_song` still picks its songs from the whole log.

### The recap

Everything in the AI's recap is counted only in shareable channels (everyone can read them and they are not NSFW) and without hidden members, and is read again on every answer:

- Message totals (this week and last week), the most talkative members and the talker, night owl and funniest titles count only shareable channels. Activity in private or NSFW channels is neither counted nor rewarded.
- Busiest channels leave out hidden members' messages.
- Nothing about music (song of the week, DJ title): the play log does not record where a song was requested, so plays started from a private channel could not be told apart.
- Words and emojis are only kept per channel, not per member, so they are shown only while nobody on the server is hidden.
- The quote of the week is the only part that is reused (for 10 minutes per server and period, since finding it fetches messages); its author and channel are checked again on every answer.

The opt-out list is read before anything that could create the community database (`get_settings` does), and again after the last await: if someone hid themselves meanwhile, or a counted channel stopped being shareable, the tool answers "not available". The weekly post's "missing regulars" are left out: a member's last message may be in a private channel, so the list would tell.

Groups are explained in [the tools factory](../tools_factory.md#tool-groups).
