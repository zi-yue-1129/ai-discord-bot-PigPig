# Community Tools

`llm/tools/community_tools.py` lets the AI answer questions about the community features (rankings, achievements, the weekly recap, birthdays and events) and act on a few of them. `llm/tools/fun_tools.py` adds dice and the decision wheel.

The AI's answer is posted for everyone in the channel, so each tool returns only what a public post would show:

- Members who hid themselves with `/leaderboard optout` are never named, and what they did is not counted (recap numbers, event sign-ups). A hidden member asking about themselves is pointed to the private slash command. The opt-out list is read with `user_stats.hidden_member_ids()`; when it cannot be read, the leaderboard and recap answer "not available", the birthday tool answers "not available" and events are listed without counts. Tools never create a missing community database before the list was read.
- Text from a channel (channel names, quotes, words, event titles) is only used when the channel is *shareable*: every member can read it (`audience_can_read`) and it is not age-restricted (NSFW, its own or its parent's). An event in the channel the answer goes to is always listed.
- Names and other text members wrote go through `user_text()`: angle brackets are replaced, `@everyone`/`@here` are broken up, links become `[link]`, the text is cut to 100 characters and wrapped in `<<< >>>` so the model reads it as data.
- Nothing here calls a model or uses anyone's chat quota.
- Tools that act only ever act for the person talking to the bot. A step that makes someone more visible needs that person's own action, so text that tricks the model cannot undo someone's choice: showing oneself on the leaderboard again is only possible with the slash command, and a birthday is saved only when the member it is for presses Save under the question `propose_birthday` posts. Making an event needs its host to press Confirm, and joining or leaving one and deleting one's birthday need the asker to press Confirm under the question the tool posts, so text that tricks the model cannot change anything on its own.

| Tool | Group | Loaded when | Arguments | Returns |
| --- | --- | --- | --- | --- |
| `get_leaderboard` | community | LeaderboardCog is loaded | `kind`: messages, streak or games; `period`: week, month or all | The top 10, as `/leaderboard top`, and the asker's own place |
| `get_achievements` | community | LeaderboardCog is loaded | `user_id` (defaults to the asker) | Unlocked achievements with dates, locked ones with what they need |
| `hide_my_stats` | core | LeaderboardCog is loaded | none | Hides the asker only. Showing oneself again is only possible with `/leaderboard optout hide:False`, so text that tricks the model cannot undo someone's choice |
| `get_server_recap` | community | CommunityCog is loaded | `period`: this_week or last_week | The weekly recap's facts (messages, shareable channels, talkers, words, quote, titles; no music) |
| `get_upcoming_birthdays` | community | CommunityCog is loaded (says so when birthdays are off for the server; building the tool list reads no database) | `days`: 1 to 30 | Saved birthdays, soonest first, without hidden members, bots or leavers |
| `remove_my_birthday` | community | CommunityCog is loaded | none | Asks the asker to confirm deleting their saved birthday; the database is only read (never created) before they press Confirm, and an unreadable one answers "not available" |
| `propose_birthday` | community | CommunityCog is loaded | `month`, `day`, `user_id` (defaults to the asker) | Posts a question with Save and Decline buttons only that member can press (see [Birthdays the AI proposes](../../cogs/community.md#birthdays-the-ai-proposes)); refused for members who declined someone else's proposal, hidden members (unless they ask for themselves), bots and members who cannot see the channel |
| `list_upcoming_events` | events | EventsCog is loaded | none | Up to 10 events: number, title, Discord start timestamp, sign-up counts (without hidden members and people who left), link |
| `create_event` | events | EventsCog is loaded | `title`, `time`, `limit`, `remind_minutes` | Posts a proposal with Confirm and Cancel buttons only the asker (the host) can press; the event is made on Confirm, within 3 minutes, with the limits checked again |
| `join_event` | events | EventsCog is loaded | `event_id`, `status`: going, maybe or leave | Asks the asker to confirm signing up or out (see [the events cog](../../cogs/events.md#events-the-ai-proposes)); refused for other servers' events, started ones and events in channels they cannot read; the model's reply never repeats the title |
| `roll_dice` | fun | always | `notation`, `reason` | Posts the roll in the channel (as `/roll`) and returns it, so the model never invents a result |
| `spin_wheel` | fun | WheelCog is loaded | `options` (2 to 20) | Spins the wheel in the channel (as `/wheel spin`), one spin per channel at a time |

### The recap

Everything in the AI's recap is counted only in shareable channels (everyone can read them and they are not NSFW) and without hidden members, and is read again on every answer:

- Message totals (this week and last week), the most talkative members and the talker, night owl and funniest titles count only shareable channels. Activity in private or NSFW channels is neither counted nor rewarded.
- Busiest channels leave out hidden members' messages.
- Nothing about music (song of the week, DJ title): the play log does not record where a song was requested, so plays started from a private channel could not be told apart.
- Words and emojis are only kept per channel, not per member, so they are shown only while nobody on the server is hidden.
- The quote of the week is the only part that is reused (for 10 minutes per server and period, since finding it fetches messages); its author and channel are checked again on every answer.

The opt-out list is read before anything that could create the community database (`get_settings` does), and again after the last await: if someone hid themselves meanwhile, or a counted channel stopped being shareable, the tool answers "not available". The weekly post's "missing regulars" are left out: a member's last message may be in a private channel, so the list would tell.

Groups are explained in [the tools factory](../tools_factory.md#tool-groups).
