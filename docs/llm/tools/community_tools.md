# Community Tools

`llm/tools/community_tools.py` lets the AI answer questions about the community features: rankings, achievements, the weekly recap, birthdays and events.

The AI's answer is posted for everyone in the channel, so each tool returns only what a public post would show:

- Members who hid themselves with `/leaderboard optout` are never named, and what they did is not counted (recap numbers, event sign-ups). A hidden member asking about themselves is pointed to the private slash command. The opt-out list is read with `user_stats.hidden_member_ids()`; when it cannot be read, the leaderboard, recap and birthday tools answer "not available" and events are listed without counts.
- Text from a channel (channel names, quotes, words, event titles) is only used when the channel is *shareable*: every member can read it (`audience_can_read`) and it is not age-restricted (NSFW, its own or its parent's). An event in the channel the answer goes to is always listed.
- Names and other text members wrote go through `user_text()`: angle brackets are replaced, `@everyone`/`@here` are broken up, links become `[link]`, the text is cut to 100 characters and wrapped in `<<< >>>` so the model reads it as data.
- Nothing here calls a model or uses anyone's chat quota.

| Tool | Group | Loaded when | Arguments | Returns |
| --- | --- | --- | --- | --- |
| `get_leaderboard` | community | LeaderboardCog is loaded | `kind`: messages, streak or games; `period`: week, month or all | The top 10, as `/leaderboard top`, and the asker's own place |
| `get_achievements` | community | LeaderboardCog is loaded | `user_id` (defaults to the asker) | Unlocked achievements with dates, locked ones with what they need |
| `hide_my_stats` | core | LeaderboardCog is loaded | none | Hides the asker only. Showing oneself again is only possible with `/leaderboard optout hide:False`, so text that tricks the model cannot undo someone's choice |
| `get_server_recap` | community | CommunityCog is loaded | `period`: this_week or last_week | The weekly recap's facts (messages, shareable channels, talkers, words, quote, song, titles, quiet regulars) |
| `get_upcoming_birthdays` | community | CommunityCog is loaded and birthdays are on for the server | `days`: 1 to 30 | Saved birthdays, soonest first, without hidden members, bots or leavers |
| `list_upcoming_events` | events | EventsCog is loaded | none | Up to 10 events: number, title, Discord start timestamp, sign-up counts (without hidden members and people who left), link |

### The recap

The recap's names (talkers, titles, the quote, quiet regulars) come from `RecapBuilder` and are reused for 10 minutes per server and period; hidden members, people who left and a quote from a channel that stopped being shareable are removed again on every answer. Every number is read again on every answer, without the hidden members:

- Message totals (this week and last week) leave out hidden members' messages, in any channel.
- Busiest channels are counted without hidden members' messages and list only shareable channels.
- The song of the week leaves out plays a hidden member requested.
- Words and emojis are only counted per channel, not per member, so they are left out when a hidden member wrote in a shareable channel that week.

After the last await, the opt-out list and the shareable channels are read again: if someone hid themselves meanwhile the tool answers "not available", and if a channel stopped being shareable while words were counted, the words and emojis are left out.

Groups are explained in [the tools factory](../tools_factory.md#tool-groups).
