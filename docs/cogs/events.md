# Events Cog Documentation

## Overview

`/event` lets members plan something together (揪團): a game night, a meal, a watch party. The bot posts the event with **Join / Maybe / Leave** buttons, keeps the list of who is coming up to date, and mentions everyone going shortly before it starts.

Events are stored in `data/events.db` (`events` and `event_signups`), so they and their buttons survive a restart.

## `/event create title time [limit] [remind]`

| Option | Meaning |
|---|---|
| `title` | What the event is (up to 100 characters) |
| `time` | When it starts, read like reminder times: `明天 20:00`, `30分鐘後`, `tomorrow 8pm`, `10/30 19:00`. Times are in the bot host's time zone; the message shows them with Discord timestamps, so everyone sees their own local time |
| `limit` | Most people who can join, 0–100 (0 = no limit) |
| `remind` | Minutes before the start to remind everyone going, 0–1440 (default 15) |

- The host is signed up as going.
- With a limit, people who join once it is full go on a **waiting list** in the order they pressed. When someone leaves, the first person waiting moves up on their own and the bot mentions only them in the channel.
- Switching to Maybe and back puts you at the end of the line; pressing Join again when already going keeps your place.
- Each answer is confirmed only to the person who pressed (ephemeral), e.g. "you're number 2 on the waiting list".
- After the start time the buttons say the event has started.

Limits: an event can be at most 180 days ahead, a member can have 5 upcoming events and a server 25.

## Events the AI proposes

The AI's `create_event` tool calls `post_draft`: it checks the title, limit, reminder and time like `/event create` and posts a proposal with Confirm and Cancel buttons. Only the host (the person who asked) can press them, within 3 minutes (`DRAFT_SECONDS`). Nothing is saved until Confirm, and `confirm_draft` checks the time and the per-member and per-server limits again; a second press is refused. If saving the host's sign-up or posting the event fails, the event is deleted again, so no event without a message counts against the limits. Each member has at most one open proposal (a new one, even for the same event, replaces it and the old one says so), and a server at most 5 (`MAX_PENDING_DRAFTS_PER_GUILD`) from different members.

The `join_event` tool calls `propose_answer`: it posts a question (pinging nobody) with Confirm and Cancel buttons from `addons/confirm.py` that only the asker can press, within 3 minutes, and one open question per member. Confirm runs `answer_for_member`, the same locked sign-up path as the buttons, only for events of this server that have not started, in channels the member can read. The question names the event by title only in the event's own channel, otherwise by number and link; a member who lands on the waiting list is not told their place in that public reply.

## Hidden members

The event message never names or counts members hidden with `/leaderboard optout`: they are left out of the going, waiting and maybe lists and their counts, and a hidden host is shown as "a member". The opt-out list is read (read-only) whenever the message is drawn; while it cannot be read the message of an open event is not updated (the answer is still saved), and a new or cancelled event's message shows nobody.

## The reminder

At `starts − remind` minutes the bot posts in the event's channel, mentioning everyone going (not the waiting list or maybes). Only those members can be pinged by it: `@everyone`, roles and other mentions in the title are never pinged. Long lists are split into several messages under Discord's 2000-character limit. Where someone who can see the channel may not read its history, the reminder (and the waiting-list message) names the event only by number with a link, not by title.

The event is marked reminded only after every message was sent. A failed reminder is tried again after a minute, at most 3 times; each message records whom it mentioned, so a retry (or a restart) mentions only the people who did not get it yet, even if someone left and joined again in between. Whether the title may be shown is decided again for every reminder message. A cancelled event is never reminded, and a button pressed while the event is being cancelled is refused. If the bot was offline past the reminder time it still reminds, saying the event has started, unless it is more than an hour past the start.

## `/event list` and `/event cancel event_id`

`/event list` shows the server's upcoming events with links (only to you), leaving out events in channels you cannot see and every event in a private thread (thread permissions follow the parent channel even though only the thread's members can read it). `/event cancel` can be used by the host or anyone with **Manage Events** who can read the event's channel (an event in a channel or private thread you cannot read is "not found"); the message is struck through and its buttons removed. Access and the right to cancel (host, or Manage Events in the event's channel) are checked again, with the member as they are now, once the cancel has the event to itself (a member who cannot be looked up may not cancel); the confirmation names the event only if you can still read its channel; and cancelling an event that was cancelled meanwhile says so instead of cancelling twice.

Who can read a channel is decided in one place, `addons/visibility.py`: a member needs to see the channel and read its history, and for a private thread also be in it (or manage threads). Whether a post may repeat the title for everyone in the channel is decided from the channel's permissions alone (`@everyone` sees and reads it, no overwrite denies either), which errs towards leaving the title out.
