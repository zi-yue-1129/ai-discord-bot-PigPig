"""Slash command groups of the music player.

The player itself lives in ``cogs/music.py`` (``YTMusic``); these cogs only add the
``/music``, ``/queue``, ``/filter``, ``/playlist`` and ``/music_settings`` commands
on top of it.
"""

from cogs.music_lib.commands.player_group import FilterCommand, MusicGroup
from cogs.music_lib.commands.playlist_group import PlaylistGroup
from cogs.music_lib.commands.queue_group import QueueGroup
from cogs.music_lib.commands.settings_group import MusicSettingsGroup


async def setup(bot):
    """Adds the music command groups."""
    for cog in (MusicGroup(bot), FilterCommand(bot), QueueGroup(bot), PlaylistGroup(bot), MusicSettingsGroup(bot)):
        await bot.add_cog(cog)
