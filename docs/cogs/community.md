# Community Cog Documentation

## Overview

The Community cog makes the bot part of the server: it welcomes new members, celebrates birthdays and yearly join anniversaries. Every feature is **off** until a server admin turns it on with `/community`. The bot owner sets the limits in the `community:` block of `base.yaml`.

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
```

## Storage

`data/community.db` (SQLite): `guild_settings`, `birthdays` (per server), `job_runs`, `birthday_roles`.

## Code

- `cogs/community.py` — the cog (listeners, scheduler, commands)
- `cogs/community_lib/store.py` — `CommunityStore`, `GuildSettings`
- `cogs/community_lib/dates.py` — local time, birthday and anniversary rules
- `cogs/community_lib/joins.py` — `JoinTracker` (batching, raids, AI budget)
- `cogs/community_lib/limits.py` — `CommunityLimits` from `base.yaml`
- `llm/announcement_writer.py` — `compose_announcement`, shared by community messages
