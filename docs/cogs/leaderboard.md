# Leaderboard Cog Documentation

## Overview

The Leaderboard cog turns the message stats that [StatsCog](stats_cog.md) already keeps into rankings, member profiles and achievements. Everyone is on the leaderboards by default; a member who does not want to be can hide themselves with `/leaderboard optout`.

Rankings only list people who are still in the server; bots and hidden members are left out. Names are shown without pinging anyone.

## Commands

| Command | What it does |
|---|---|
| `/leaderboard top [period] [kind]` | Top 10 by messages this week (default), this month or all time, by current daily streak, or by game points (see [Games](games.md)). Shows your own place when you are outside the top 10 |
| `/leaderboard optout hide` | `True` hides you from leaderboards, weekly recaps and achievement announcements; `False` shows you again |
| `/profile [user]` | Activity card (messages, active hours, public channels), all-time rank and badges |
| `/achievements [user]` | Every achievement, unlocked (with the date) or locked, and what it takes |

A hidden member's profile and achievements are only shown to themselves, privately. Words and emojis are not on the card: the all-time counts do not record which channel they came from, so they could reveal what was said in private channels.

Weeks start on Monday and months on the 1st, in the server's time zone (`/community timezone`). Week and month counts come from the dashboard's `message_events`; all-time counts and streaks from `user_stats`. A streak counts only while it is alive (a message today or yesterday).

## Achievements

After each message StatsCog dispatches `user_stats_updated` with the member's fresh stats, and the cog unlocks every achievement whose requirements are all met.

| ID | Name (zh_TW) | Requirement |
|---|---|---|
| `msg_100` 💬 | 話匣子 | 100 messages |
| `msg_1000` 📜 | 千言萬語 | 1,000 messages |
| `msg_10000` 📚 | 萬言書 | 10,000 messages |
| `streak_7` 📅 | 一週全勤 | 7-day streak |
| `streak_30` 🏅 | 全勤獎 | 30-day streak |
| `night_owl` 🦉 | 夜貓子 | 40% of messages between 0:00 and 4:59, with at least 200 messages |
| `diver` 🤿 | 潛水大師 | Speak again after 30 days of silence |
| `revived` 🧟 | 死而復生 | Speak again after 180 days of silence |
| `veteran` 📼 | 古董成員 | 365 days since the first message |

Announcements are **off** until an admin picks a mode with `/community achievements`:

- `reply`: a 🏆 reaction and a short reply on the message that unlocked it.
- `channel`: one line in the community announcement channel.

A member gets at most one announcement a day (several unlocks are combined), and hidden members are never announced. The first time a member is checked, achievements they had already earned before this feature existed are recorded quietly, so turning the feature on does not flood the server; only "came back after a long silence" ones, which that very message earned, are announced.

Rotating weekly titles (本週話王, 夜貓王, 笑點製造機, 本週 DJ) are handed out by the [weekly recap](community.md#weekly-recap) and shown on `/profile`.

## Owner settings (`base.yaml`)

The bot owner can replace the built-in list:

```yaml
community:
  achievements:
    - id: msg_500
      emoji: "🗣️"
      name: "Five hundred"
      description: "Send 500 messages"   # optional; generated from "when" if left out
      when: {total_messages: 500}
```

Stats available in `when`: `total_messages`, `streak_days`, `gap_days`, `night_ratio` (0–1), `membership_days`. Entries with unknown stats or non-numeric values are skipped with a warning. Built-in IDs without a `name` keep their translated names.

## Code

- `cogs/leaderboard.py` — the cog (commands, achievement listener)
- `cogs/community_lib/achievements.py` — definitions, `load_achievements`, `stat_values`, `reached`
- `cogs/community_lib/store.py` — opt-outs and unlocked achievements in `data/community.db`
- `cogs/memory/db/stats_storage.py` — `get_guild_rankings`
- `dashboard/services/stats_collector.py` — `message_counts_by_user`
