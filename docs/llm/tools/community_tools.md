# Community Tools

`llm/tools/community_tools.py` lets the AI answer questions about the community features: rankings, achievements, the weekly recap, birthdays and events.

The AI's answer is posted for everyone in the channel, so each tool returns only what a public post would show:

- Members who hid themselves with `/leaderboard optout` are never named. A hidden member asking about themselves is pointed to the private slash command.
- Text from a channel (channel names, quotes, words, event titles) is only used when every member can read that channel, or when it is the channel the answer goes to.
- Names and other text members wrote are wrapped in `<<< >>>` so the model reads them as data.
- Nothing here calls a model or uses anyone's chat quota.

| Tool | Group | Loaded when | Arguments | Returns |
| --- | --- | --- | --- | --- |
| `get_leaderboard` | community | LeaderboardCog is loaded | `kind`: messages, streak or games; `period`: week, month or all | The top 10, as `/leaderboard top`, and the asker's own place |
| `get_achievements` | community | LeaderboardCog is loaded | `user_id` (defaults to the asker) | Unlocked achievements with dates, locked ones with what they need |
| `set_my_stats_visibility` | core | LeaderboardCog is loaded | `hide` | Hides or shows the asker only; it has no member argument |
| `get_server_recap` | community | CommunityCog is loaded | `period`: this_week or last_week | The weekly recap's facts (messages, public channels, talkers, words, quote, song, titles, quiet regulars) |
| `get_upcoming_birthdays` | community | CommunityCog is loaded and birthdays are on for the server | `days`: 1 to 30 | Saved birthdays, soonest first, without hidden members, bots or leavers |
| `list_upcoming_events` | events | EventsCog is loaded | none | Up to 10 events: number, title, Discord start timestamp, roster counts, link |

A built recap is reused for 10 minutes per server and period. Hidden members and channels that stopped being public are removed again on every answer, so the cache never shows something a fresh recap would leave out.

Groups are explained in [the tools factory](../tools_factory.md#tool-groups).
