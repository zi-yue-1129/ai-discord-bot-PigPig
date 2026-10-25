# Music Commands, Player and Server Settings

**Location:** [`cogs/music_commands.py`](../../cogs/music_commands.py) (command groups in
[`cogs/music_lib/commands/`](../../cogs/music_lib/commands/)), on top of the `YTMusic` player in
[`cogs/music.py`](./music.md).

This page covers the commands added next to `/play`, `/mode`, `/shuffle`, `/volume`,
`/queue_remove` and `/queue_clear`, the player interface, and the per-server music settings.

## Commands

### `/music` — playback position, history, lyrics

| Command | What it does |
| --- | --- |
| `/music seek time` | Jump to a time of the current song (`1:30`, `90` or `1:02:03`). |
| `/music forward [seconds]` / `/music rewind [seconds]` | Skip ahead / go back (10 s by default). |
| `/music replay` | Start the current song over. |
| `/music previous` | Go back to the song played before (the current one plays again after it). |
| `/music history` | The songs played in this session, newest first. |
| `/music lyrics [query]` | Lyrics of the current song (or of a song you name), paged. Time-stamped lyrics offer a button to show them synced on the player. |

### `/filter effect`

Applies an FFmpeg audio effect to the current song (restarted where it was) and to the following
songs, until it is turned off or the bot leaves the channel: nightcore, vaporwave, slowed + reverb,
8D, bass boost, karaoke (vocals removed), soft, tremolo, vibrato, 1.25x speed, 0.8x speed. The presets
live in [`cogs/music_lib/filters.py`](../../cogs/music_lib/filters.py).

### `/queue` — reorder, export, import

| Command | What it does |
| --- | --- |
| `/queue move position to` | Move a queued song. |
| `/queue swap first second` | Swap two queued songs. |
| `/queue export` | The current song and the queue as a text file (one link per line). |
| `/queue import file [shuffle]` | Queue the songs of such a file. Only YouTube/SoundCloud links are opened. |

### `/playlist` — saved playlists

Every command takes `scope`: **personal** (default; follows you to every server) or **server**
(shared by the server). Anyone can view and play server playlists; only server managers and the DJ
role can change them.

`create`, `delete`, `rename`, `list`, `view`, `add [query]` (no query = the song that is playing; a
playlist link adds all its songs), `remove position`, `play [shuffle]`, `save_queue`,
`share user` (gives the other user their own copy), `export`, `import file`.

### `/music_settings` — server settings (Manage Server permission)

| Command | Setting |
| --- | --- |
| `/music_settings view` | Show the settings. |
| `/music_settings dj [role]` | DJ role; empty removes it (everyone in the channel controls the music, as before). |
| `/music_settings vote_ratio percent` | Share of the listeners whose votes skip a song (default 50%). |
| `/music_settings default_volume percent` | Volume each voice session starts at. |
| `/music_settings stay_247 enabled [channel]` | Stay in the voice channel when the queue ends or the channel empties; rejoins after a restart. |
| `/music_settings request_channel [channel]` | Song request channel (see below); empty turns it off. |
| `/music_settings stage_announce enabled` | In a stage channel, set the stage topic to the song that plays. |

The same settings are on the dashboard's **Music** tab of each server
(`GET`/`PUT /api/guild/{guild_id}/music`).

## Who may control the music

Without a DJ role, everyone in the bot's voice channel may (unchanged behaviour). With a DJ role:

* DJs, server managers, and whoever is alone with the bot control everything.
* Everyone else may add songs, view the queue and lyrics, and remove **their own** queued songs.
* Skipping: the requester of the current song skips it right away; other listeners vote, and the
  song is skipped once the configured share of the listeners voted.

## The player interface

```
⏮️ ⏯️ ⏭️ ⏹️ 🎤
🔀 📜 🎶 ⏪ ⏩
[📜 Pick a queued song…]   → privately: [Play next] [Remove]
[➡️ Loop mode]
[🎛️ Audio effect]
```

* ⏮️ goes back through the session history (or starts the song over when there is none).
* 🎤 shows the synced lyrics on the player. The player message is edited as soon as the sung line changes
  (the position is checked twice a second, and edits are at least one second apart). Among the lyrics found, the
  ones with time stamps and a length closest to the song's win; an entry whose length is unknown ranks after the
  ones known to fit. If the lines come out ahead of or behind the singing, `lyrics.offset_seconds` in
  `music.yaml` shifts all of them (negative shows them later).
* ⏪ ⏩ jump 10 seconds.

## Song request channel

Every message in the request channel is treated as `/play <message>` by its author and then deleted,
so the channel only shows the pinned explanation and the player. The AI does not chat in that
channel.

## AI tools

Besides playing and controlling music, the AI can `seek_music`, `set_music_effect`,
`play_previous_song`, `move_song_in_queue`, `get_current_song_lyrics` (only when asked about the
lyrics), `play_saved_playlist` and `add_song_to_playlist`. See
[`llm/tools/music_tools.py`](../../llm/tools/music_tools.py).

## Configuration (`music.yaml`)

```yaml
library:
  database_path: "data/music/music.db"   # server settings and playlists
  max_playlists: 25                      # per user / per server
  max_playlist_tracks: 200

lyrics:
  enabled: true
  api_url: "https://lrclib.net/api"      # LRCLIB: free, no API key
  timeout_seconds: 10
  offset_seconds: 0.0                    # negative = show the lines later
```
