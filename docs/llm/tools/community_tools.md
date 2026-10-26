# Community Tools

`llm/tools/community_tools.py` lets the AI answer questions about the community features: rankings, achievements, the weekly recap, birthdays and events.

The AI's answer is posted for everyone in the channel, so each tool returns only what a public post would show:

- Members who hid themselves with `/leaderboard optout` are never named, and what they did is not counted (recap numbers, event sign-ups). A hidden member asking about themselves is pointed to the private slash command. The opt-out list is read with `user_stats.hidden_member_ids()`; when it cannot be read, the leaderboard and recap answer "not available", the birthday tool is not offered and events are listed without counts. Tools never create a missing community database before the list was read.
- Text from a channel (channel names, quotes, words, event titles) is only used when the channel is *shareable*: every member can read it (`audience_can_read`) and it is not age-restricted (NSFW, its own or its parent's). An event in the channel the answer goes to is always listed.
- Names and other text members wrote go through `user_text()`: angle brackets are replaced, `@everyone`/`@here` are broken up, links become `[link]`, the text is cut to 100 characters and wrapped in `<<< >>>` so the model reads it as data.
- Nothing here calls a model or uses anyone's chat quota.

| Tool | Group | Loaded when | Arguments | Returns |
| --- | --- | --- | --- | --- |
| `get_leaderboard` | community | LeaderboardCog is loaded | `kind`: messages, streak or games; `period`: week, month or all | The top 10, as `/leaderboard top`, and the asker's own place |
| `get_achievements` | community | LeaderboardCog is loaded | `user_id` (defaults to the asker) | Unlocked achievements with dates, locked ones with what they need |
| `hide_my_stats` | core | LeaderboardCog is loaded | none | Hides the asker only. Showing oneself again is only possible with `/leaderboard optout hide:False`, so text that tricks the model cannot undo someone's choice |
| `get_server_recap` | community | CommunityCog is loaded | `period`: this_week or last_week | The weekly recap's facts (messages, shareable channels, talkers, words, quote, song, titles) |
| `get_upcoming_birthdays` | community | CommunityCog is loaded and birthdays are on for the server | `days`: 1 to 30 | Saved birthdays, soonest first, without hidden members, bots or leavers |
| `list_upcoming_events` | events | EventsCog is loaded | none | Up to 10 events: number, title, Discord start timestamp, sign-up counts (without hidden members and people who left), link |

### The recap

Everything in the AI's recap is counted only in shareable channels (everyone can read them and they are not NSFW) and without hidden members, and is read again on every answer:

- Message totals (this week and last week), the most talkative members and the talker, night owl and funniest titles count only shareable channels. Activity in private or NSFW channels is neither counted nor rewarded.
- Busiest channels leave out hidden members' messages; the song of the week and the DJ title leave out what hidden members requested.
- Words and emojis are only kept per channel, not per member, so they are shown only while nobody on the server is hidden.
- The quote of the week is the only part that is reused (for 10 minutes per server and period, since finding it fetches messages); its author and channel are checked again on every answer.

The opt-out list is read before anything that could create the community database (`get_settings` does), and again after the last await: if someone hid themselves meanwhile, or a counted channel stopped being shareable, the tool answers "not available". The weekly post's "missing regulars" are left out: a member's last message may be in a private channel, so the list would tell.

Groups are explained in [the tools factory](../tools_factory.md#tool-groups).
