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

## The reminder

At `starts − remind` minutes the bot posts in the event's channel, mentioning everyone going (not the waiting list or maybes). Only those members can be pinged by it: `@everyone`, roles and other mentions in the title are never pinged. Long lists are split into several messages under Discord's 2000-character limit. Where someone who can see the channel may not read its history, the reminder (and the waiting-list message) names the event only by number with a link, not by title.

The event is marked reminded only after every message was sent. A failed reminder is tried again after a minute, at most 3 times; each message records whom it mentioned, so a retry (or a restart) mentions only the people who did not get it yet, even if someone left and joined again in between. A cancelled event is never reminded, and a button pressed while the event is being cancelled is refused. If the bot was offline past the reminder time it still reminds, saying the event has started, unless it is more than an hour past the start.

## `/event list` and `/event cancel event_id`

`/event list` shows the server's upcoming events with links (only to you), leaving out events in channels you cannot see and every event in a private thread (thread permissions follow the parent channel even though only the thread's members can read it). `/event cancel` can be used by the host or anyone with **Manage Events** who can read the event's channel (an event in a channel or private thread you cannot read is "not found"); the message is struck through and its buttons removed.

Who can read a channel is decided in one place, `addons/visibility.py`: a member needs to see the channel and read its history, and for a private thread also be in it (or manage threads).
