# Community Cog Documentation

## Overview

The Community cog makes the bot part of the server: it welcomes new members, celebrates birthdays and yearly join anniversaries, and posts a weekly recap, and notices when several members play the same game. Every feature is **off** until a server admin turns it on with `/community`. The bot owner sets the limits in the `community:` block of `base.yaml`.

Messages are written by the model in the bot's own voice (the server's persona). Whenever the model is unavailable, over its budget, or the server is being raided, a fixed translated text is posted instead, so nothing is lost. Only the people being welcomed or celebrated can be pinged; `@everyone` and role pings are always blocked.

## Admin commands (`/community`, needs Manage Server)

| Command | What it does |
|---|---|
| `/community status` | Shows every setting |
| `/community channel channel` | Default channel for announcements (otherwise the server's system channel) |
| `/community timezone [name]` | IANA time zone such as `Asia/Taipei` for daily messages; empty uses the owner's default |
| `/community welcome enabled [channel] [note] [farewell]` | Turns welcomes on or off. `note` is something every welcome should point out (rules channel, intro channel). `farewell` also posts a short line when someone leaves |
| `/community welcome_test` | Previews the welcome with yourself as the new member (only you see it) |
| `/community birthdays enabled [hour] [role]` | Celebrates saved birthdays at `hour` (local, default 9). `role` is given for the day and taken back at midnight |
| `/community anniversaries enabled` | Celebrates members who joined on this day in an earlier year (at the same hour) |
| `/community weekly enabled [channel] [day] [hour]` | Posts the weekly recap (default Sunday 20:00, local) |
| `/community weekly_preview` | Shows this week's recap so far, only to you |
| `/community playing enabled [channel] [min_players]` | Points out when at least `min_players` members (default 3) play the same game; see [What everyone is playing](#what-everyone-is-playing) |
| `/community achievements mode` | How unlocked achievements are announced: `off` (default), `reply` (🏆 reaction and a short reply) or `channel` (announcement channel). See [Leaderboards & Achievements](leaderboard.md) |

## Member commands (`/birthday`)

| Command | What it does |
|---|---|
| `/birthday set month day` | Saves your birthday **on this server only** (no year asked) |
| `/birthday remove` | Removes it |
| `/birthday upcoming` | Lists birthdays in the next 30 days |

Feb 29 birthdays and join dates are celebrated on Feb 28 in common years.

## Welcomes

- Joins within `batch_seconds` of each other share one message.
- When `burst_threshold` members join within `burst_seconds`, the server is treated as raided: the fixed text is used and the model is not called.
- At most `max_ai_per_hour` AI-written welcomes per server per hour; later ones use the fixed text.
- Bots are never welcomed.

## Daily messages

A background check runs every 5 minutes. Once the server's local hour reaches the configured hour, today's birthday and anniversary messages are posted, once per day (recorded in `job_runs`, so a restart neither repeats nor loses them). Several people on the same day share one message, naming at most `max_mentions` of them.

A job that fails (Discord error, no channel to post in yet) is retried while it is still due, waiting 5 minutes and then twice as long each time, up to an hour; it is only recorded as done once it succeeds. The wait is kept in memory, so after a restart a failing job is tried once right away.

The birthday role must be one the admin could hand out themselves (Manage Roles and a higher role, or the server owner), the bot must have Manage Roles, and roles with moderator permissions (including mute, deafen and move members) are refused. The role is checked again each time it is given. Members who already had the role keep it after their birthday.

## Weekly recap

Once a week, at the configured day and hour, one embed sums up the week (Monday 00:00 to now, server time):

- Messages this week, compared with the same span last week
- The 3 busiest channels and the 3 most talkative members
- Top emojis and hot words of the week
- **Quote of the week**: the most reacted message that still exists, with a jump link
- **Song of the week**: the most played song (at least 2 plays, fewer than half skipped)
- **Rotating titles**: 🎤 本週話王 (most messages), 🌙 夜貓王 (most messages between 0:00 and 4:59), 😂 笑點製造機 (most reactions received), 🎧 本週 DJ (most songs requested). Titles move to the new holders each week and show on `/profile`
- **Missing in action**: up to 3 former regulars (`missing_min_messages`) who have been silent for `missing_after_days`
- An AI-written news paragraph on top, in the server persona; the plain numbers are posted when the model is unavailable

Only channels everyone can read (`@everyone` can view the channel and read its history) count toward the busiest channels, hot words, top emojis and the quote of the week; private channels never show up in the recap. Threads count when they are public and in the bot's cache: an archived thread is left out (its words and quotes are dropped, never leaked).

Members who opted out with `/leaderboard optout` are never named, quoted or given a title. Weeks with fewer than `min_messages` messages are skipped. If the bot was down at the scheduled time, the recap is still posted within 24 hours, once (`job_runs`).

## What everyone is playing

When at least `min_players` members have each been playing the same game for `min_minutes` (from their Discord presence; only games count, not Spotify, streams or custom statuses), and they are not already all in one voice channel, the bot posts one line in the chosen channel naming them, e.g. "A, B and C are all playing Valorant. Want to team up in voice?". Games are matched by name, ignoring case and spacing.

- Only members who can see that channel are named and counted, and members who opted out with `/leaderboard optout` never are. Bots never count.
- The same game is pointed out at most once every `cooldown_hours` per server, and a server gets at most `max_per_day` posts in 24 hours. A post that could not be sent is tried again after 10 minutes.
- The line is written by the model in the server persona (the game's name is passed as data, never as instructions), or a fixed text when `use_ai` is off or the model fails. Only the named players are pinged.
- Players are checked again right before the post is sent (still playing, can see the channel, not opted out); the written text is replaced by the fixed one when someone dropped out, and nothing is posted when too few are left. The minimum is counted over everyone who qualifies; the post names the first `max_mentions` of them. Game names are shown without links (invites such as `discord.gg/…` included), mentions, line breaks or formatting, after folding look-alike characters (such as `＠`) and removing invisible ones; a bare domain like `agar.io` keeps its name but its dots can't form a link, and link previews are off. A written post that misses a player's mention (after it is cut to length), mentions anyone else, or contains a link or domain is replaced by the fixed text. Right before sending, the settings are read again: nothing is posted if the feature was turned off or its channel changed, the daily cap was reached or lowered, the game is in its cooldown, fewer players qualify than `min_players` now asks for, or they have meanwhile joined one voice channel. A post is recorded just before it is sent, so it counts for the cooldown and the daily cap even if the database fails afterwards.
- When the bot has **Manage Channels** where the post goes, it carries an **Open a voice room** button for members who can see the channel and are not timed out. It creates one temporary voice channel per post (once: a closed room is not opened again, and nothing opens once the feature is off), next to the post's channel and open to the same people (it inherits a synced category's permissions, or copies the channel's own). A server has at most `max_rooms` such rooms at once. A room is deleted as soon as the last person leaves, or after `room_idle_minutes` if nobody joined. The button stops working after `cooldown_hours` (at least 10 minutes), and opens nothing while `max_per_day` is 0. A post claims its room in the database before the room is created (together with the room limit, counting rooms other posts are opening), so it opens at most one room and the limit holds, also across a reload of the cog; unloading the cog waits for a room being opened, a creation Discord refused frees its claim at once, one that timed out keeps it until it is stale (Discord may have made the room anyway: a room is named after its game and ends in the claim's token, ` · #a1b2c3d4e5f60718` (16 characters), so when its event arrives, when the request gives up, and before a claim is freed, the bot looks for a channel carrying the token of a claim that is still open and records it. Only a channel made after the claim (Discord's clock and the bot's may differ by up to 10 seconds) is taken in: one without the token, with the token of a claim that is gone, with a token two open claims share, with a post that has its room on record already, or an older channel that was renamed is left alone and never deleted. A claim whose room was marked used but could not be recorded keeps its token, so a reloaded cog still finds the room; the token is taken away as soon as that room is closed or found gone (a write that fails is retried by the regular check), and the claims of a server that is unavailable are neither freed nor dropped with their old posts until it is back (nothing of it is cached to look through); the other servers' claims are freed as usual. The token appears only in the name of the bot's own room, so the one way to pass for it is a member who can manage channels and sees that name before the bot's own scan does; nothing is ever deleted that such a member could not delete themselves. A claim whose room exists but could not be recorded is neither freed nor dropped with its old post until it can be), a press whose claim was taken over meanwhile deletes its own room, a post is marked used for good as soon as its room exists, a press while the room is still being opened is told to try again in a minute, and one left by a stopped bot (also from an older database) is freed after three minutes, on load or by the regular check. A post recorded for a send that never finished stops counting after 10 minutes, also after a restart. The post points to its room as soon as the room exists. A room that could neither be recorded nor deleted again is kept in memory (it still uses up its post and counts towards `max_rooms`) and deleted by the next cleanup. Posts are kept for two days, or longer when `cooldown_hours` is longer; `cooldown_hours` is capped at 720.

Presences are only kept in memory (who plays which game since when); nothing about them is written to disk. The bot already needs the presences intent for its member lookup tool.

## Owner settings (`base.yaml`)

```yaml
community:
  default_timezone: ""        # e.g. "Asia/Taipei"; empty uses this machine's time zone
  welcome:
    max_ai_per_hour: 20
    burst_threshold: 5
    burst_seconds: 60
    batch_seconds: 5
  birthday:
    use_ai: true
    max_mentions: 20
  weekly:
    min_messages: 50
    use_ai: true
    max_report_chars: 300
    missing_after_days: 30
    missing_min_messages: 50
    missing_max: 3
  playing:
    min_minutes: 10
    cooldown_hours: 3
    max_per_day: 5            # 0 turns the feature off
    use_ai: true
    max_mentions: 10
    max_rooms: 3              # 0: no voice room button
    room_idle_minutes: 5
```

## Storage

`data/community.db` (SQLite): `guild_settings`, `birthdays` (per server), `job_runs`, `birthday_roles`, and for the leaderboard cog `optouts`, `user_achievements`, `achievement_checked`, `titles`, plus `playing_posts` (posts of the last two days, for the cooldown, the daily cap and the button) and `temp_voice_rooms` (rooms the bot opened and still has to delete). Columns added later (such as `achievement_mode`) are added to older files on first use.

## Code

- `cogs/community.py` — the cog (listeners, scheduler, commands)
- `cogs/community_lib/store.py` — `CommunityStore`, `GuildSettings`
- `cogs/community_lib/dates.py` — local time, birthday and anniversary rules
- `cogs/community_lib/joins.py` — `JoinTracker` (batching, raids, AI budget)
- `cogs/community_lib/limits.py` — `CommunityLimits` from `base.yaml`
- `cogs/community_lib/recap.py` — weekly recap timing, numbers and layout
- `cogs/playing.py` — `PlayingCog` (what everyone is playing, voice rooms)
- `cogs/community_lib/playing.py` — `PlayingTracker` (who plays which game, from presences)
- `addons/presence.py` — `current_game`, shared with the member lookup tool
- `llm/announcement_writer.py` — `compose_announcement`, shared by community messages
