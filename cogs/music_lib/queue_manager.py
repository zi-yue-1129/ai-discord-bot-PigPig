import asyncio
import os
import random
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
from addons.logging import get_logger
log = get_logger(source=__name__, server_id="system")
logger = log

class PlayMode(Enum):
    NO_LOOP = "no_loop"
    LOOP_QUEUE = "loop_queue"
    LOOP_SINGLE = "loop_single"

class QueueManager:
    MAX_QUEUE_SIZE = 50
    
    def __init__(self, bot=None):
        self.bot = bot
        self.guild_queues: Dict[int, asyncio.Queue] = {}
        self.guild_settings: Dict[int, Dict[str, Any]] = {}
        self.guild_playlists: Dict[int, List[Dict[str, Any]]] = {}
        # Songs already played in the current round of loop-queue mode, waiting for the next round.
        self.guild_finished: Dict[int, List[Dict[str, Any]]] = {}
        # Deliberately unseeded: a seeded shuffle would play the same order every time.
        # Tests replace it with a seeded generator.
        self._rng = random.Random()

    def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get server playback settings."""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                "play_mode": PlayMode.NO_LOOP.value,
                "shuffle": False
            }
        return self.guild_settings[guild_id]

    def get_guild_queue_and_folder(self, guild_id: int) -> Tuple[asyncio.Queue, str]:
        """Ensure the server has a unique folder and playlist."""
        if guild_id not in self.guild_queues:
            self.guild_queues[guild_id] = asyncio.Queue()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        guild_folder = os.path.join(base_dir, "temp", "music", str(guild_id))
        os.makedirs(guild_folder, exist_ok=True)
        return self.guild_queues[guild_id], guild_folder

    def get_queue(self, guild_id: int) -> asyncio.Queue:
        """Get the queue for the guild."""
        q, _ = self.get_guild_queue_and_folder(guild_id)
        return q

    def clear_guild_data(self, guild_id: int):
        """Clear the playlist for the specified server."""
        if guild_id in self.guild_queues:
            self.guild_queues[guild_id] = asyncio.Queue()
        if guild_id in self.guild_settings:
            self.guild_settings[guild_id]["play_mode"] = PlayMode.NO_LOOP.value
            self.guild_settings[guild_id]["shuffle"] = False
        if guild_id in self.guild_playlists:
            self.guild_playlists[guild_id] = []
        self.guild_finished.pop(guild_id, None)

    def set_playlist(self, guild_id: int, video_infos: List[Dict[str, Any]]):
        """Set the server's playlist."""
        self.guild_playlists[guild_id] = video_infos

    def extend_playlist(self, guild_id: int, video_infos: List[Dict[str, Any]]) -> None:
        """Appends songs to the buffered playlist instead of replacing what is still buffered."""
        self.guild_playlists.setdefault(guild_id, []).extend(video_infos)

    async def get_next_playlist_songs(self, guild_id: int, count: int = 1, youtube_manager=None, folder: Optional[str] = None, interaction=None) -> List[Dict[str, Any]]:
        """Get the next song from the playlist."""
        if guild_id not in self.guild_playlists:
            return []
        
        songs = self.guild_playlists[guild_id][:count]
        self.guild_playlists[guild_id] = self.guild_playlists[guild_id][count:]
        
        if youtube_manager and folder and interaction:
            downloaded_songs = []
            for song in songs:
                if "file_path" not in song:
                    video_info, error = await youtube_manager.download_audio(song["url"], folder, interaction)
                    if video_info:
                        downloaded_songs.append(video_info)
                else:
                    downloaded_songs.append(song)
            return downloaded_songs
        
        return songs

    def has_playlist_songs(self, guild_id: int) -> bool:
        """Check if there are more songs in the playlist."""
        return guild_id in self.guild_playlists and len(self.guild_playlists[guild_id]) > 0

    def shuffled(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Returns a shuffled copy of ``items``."""
        copy = list(items)
        self._rng.shuffle(copy)
        return copy

    def shuffle_queue(self, guild_id: int) -> None:
        """Shuffles the whole list: the queue and the playlist songs still buffered."""
        queue = self.guild_queues.get(guild_id)
        if queue is not None and len(queue._queue) > 1:
            items = self.shuffled(list(queue._queue))
            queue._queue.clear()
            queue._queue.extend(items)
        if self.guild_playlists.get(guild_id):
            self.guild_playlists[guild_id] = self.shuffled(self.guild_playlists[guild_id])

    def toggle_shuffle(self, guild_id: int) -> bool:
        """Toggles shuffle; turning it on shuffles the whole list right away."""
        settings = self.get_guild_settings(guild_id)
        settings["shuffle"] = not settings["shuffle"]
        if settings["shuffle"]:
            self.shuffle_queue(guild_id)
        return settings["shuffle"]

    def finish_for_cycle(self, guild_id: int, song: Dict[str, Any]) -> None:
        """Parks a song that was played in loop-queue mode until the next round starts."""
        self.guild_finished.setdefault(guild_id, []).append(song)

    def restart_cycle(self, guild_id: int) -> int:
        """Starts the next loop-queue round: puts the played songs (shuffled if enabled) back.

        Returns:
            How many songs were put back into the queue.
        """
        finished = self.guild_finished.pop(guild_id, [])
        if self.is_shuffle_enabled(guild_id):
            finished = self.shuffled(finished)
        self.get_queue(guild_id)._queue.extend(finished)
        return len(finished)

    def set_play_mode(self, guild_id: int, mode: PlayMode):
        """Set the playback mode."""
        settings = self.get_guild_settings(guild_id)
        settings["play_mode"] = mode.value

    def get_play_mode(self, guild_id: int) -> PlayMode:
        """Get the playback mode."""
        settings = self.get_guild_settings(guild_id)
        return PlayMode(settings["play_mode"])

    def is_shuffle_enabled(self, guild_id: int) -> bool:
        """Check if shuffle playback is enabled."""
        settings = self.get_guild_settings(guild_id)
        return settings["shuffle"]

    async def copy_queue(self, guild_id: int, shuffle: bool = False) -> Tuple[List[Dict[str, Any]], asyncio.Queue]:
        """Copy queue contents without consuming the original queue."""
        queue = self.guild_queues.get(guild_id)
        if not queue:
            return [], asyncio.Queue()
            
        queue_copy = []
        temp_queue = asyncio.Queue()
        original_queue = asyncio.Queue()
        
        while not queue.empty():
            item = await queue.get()
            queue_copy.append(item)
        
        items_to_queue = queue_copy.copy()
        if shuffle:
            random.shuffle(items_to_queue)
        
        for item in items_to_queue:
            await temp_queue.put(item)
        for item in queue_copy:
            await original_queue.put(item)
        
        self.guild_queues[guild_id] = original_queue
        
        return queue_copy, temp_queue

    def get_queue_snapshot(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get a snapshot of the current playback queue."""
        queue = self.guild_queues.get(guild_id)
        if not queue or queue.empty():
            return []
        return list(queue._queue).copy()

    def remove_at(self, guild_id: int, index: int) -> Optional[Dict[str, Any]]:
        """Remove and return the queued song at a zero-based index.

        Args:
            guild_id: The guild whose queue is edited.
            index: Zero-based position in the queue.

        Returns:
            The removed song, or ``None`` if the index is outside the queue.
        """
        queue = self.guild_queues.get(guild_id)
        if queue is None or not 0 <= index < len(queue._queue):
            return None
        song = queue._queue[index]
        del queue._queue[index]
        return song

    def move_to_front(self, guild_id: int, index: int) -> Optional[Dict[str, Any]]:
        """Moves the queued song at a zero-based index to the front, so it plays next.

        Args:
            guild_id: The guild whose queue is edited.
            index: Zero-based position in the queue.

        Returns:
            The moved song, or ``None`` if the index is outside the queue.
        """
        queue = self.guild_queues.get(guild_id)
        if queue is None or not 0 <= index < len(queue._queue):
            return None
        song = queue._queue[index]
        del queue._queue[index]
        queue._queue.appendleft(song)
        return song

    def is_queue_empty(self, guild_id: int) -> bool:
        """Check if the queue is empty."""
        q = self.guild_queues.get(guild_id)
        return not q or q.empty()

    def clear_queue(self, guild_id: int):
        """Clear the playback queue for the specified server."""
        if guild_id in self.guild_queues:
            self.guild_queues[guild_id] = asyncio.Queue()
        self.guild_finished.pop(guild_id, None)

    def set_queue(self, guild_id: int, q: asyncio.Queue):
        """Set the queue for a specific guild."""
        self.guild_queues[guild_id] = q

    async def add_to_queue(self, guild_id: int, item: Dict[str, Any], force: bool = False) -> bool:
        """
        Add an item to the queue and apply different priority logic based on the adder (user or bot).
        Returns True on success, False on failure.
        """
        q = self.get_queue(guild_id)
        # Directly manipulate q._queue (deque) to ensure atomicity

        # 1. Determine if the adder is a user or a bot
        added_by_user = 'added_by' in item and item['added_by'] != self.bot.user.id

        # 2. A song that is already queued is left alone, except that a user's request for a
        #    song the bot recommended turns it into a request (and moves it into place).
        if not force:
            video_id = item.get('video_id')
            existing = next((song for song in q._queue if song.get('video_id') == video_id), None)
            if existing is not None:
                if not (added_by_user and existing.get('added_by') == self.bot.user.id):
                    logger.info(f"Song '{item.get('title')}' is already in the queue, treating as success.")
                    return True
                if existing.get('file_path') and not item.get('file_path'):
                    item['file_path'] = existing['file_path']
                q._queue.remove(existing)

        # 3. Handle queue full scenarios
        if q.qsize() >= self.MAX_QUEUE_SIZE:
            if added_by_user:
                # User add: Search backwards from the end and delete the first bot-added song
                bot_song_removed = False
                for i in range(len(q._queue) - 1, -1, -1):
                    if q._queue[i].get('added_by') == self.bot.user.id:
                        del q._queue[i]
                        bot_song_removed = True
                        logger.info("Queue is full; removed one bot-added song for the user.")
                        break
                
                if not bot_song_removed:
                    logger.info(f"Queue is full and no bot songs to remove (guild_id: {guild_id}). Cannot add song.")
                    return False
            else:
                # Bot add: Queue is full, fail immediately
                logger.info(f"Queue is full (guild_id: {guild_id}); bot cannot add song.")
                return False

        # 4. Determine insertion point
        if added_by_user:
            # User add: Find the index of the first bot song and insert before it
            insert_index = -1
            for i, song in enumerate(q._queue):
                if song.get('added_by') == self.bot.user.id:
                    insert_index = i
                    break
            
            if insert_index != -1:
                q._queue.insert(insert_index, item)
            else:
                # If no bot songs, add to the end
                q._queue.append(item)
        else:
            # Bot add: Add directly to the end
            q._queue.append(item)

        # 5. Rebuilding queue is no longer necessary
        return True

    async def enqueue_request(self, guild_id: int, item: Dict[str, Any], play_next: bool = False) -> bool:
        """Queues a user's song request.

        Requests play in the order they were made (after earlier requests, before the bot's
        own recommendations). ``play_next`` cuts in: the song plays right after the current one.

        Args:
            guild_id: The guild.
            item: The song entry; ``added_by`` is the requesting user.
            play_next: Whether to cut in at the front of the queue.

        Returns:
            True when the song is queued, False when the queue is full.
        """
        if play_next:
            return await self.add_to_front_of_queue(guild_id, item)
        return await self.add_to_queue(guild_id, item)

    async def add_to_front_of_queue(self, guild_id: int, item: Dict[str, Any]) -> bool:
        """Add item to the front of the queue and handle overflow. Returns True on success, False on failure."""
        q = self.get_queue(guild_id)
        # Directly manipulate q._queue (deque) to ensure atomicity

        # 1. Check if the song already exists
        video_id = item.get('video_id')
        existing = next((song for song in q._queue if song.get('video_id') == video_id), None)
        if existing is not None:
            # A request for a song that is already queued (for example one the bot recommended)
            # makes it the requester's song and plays it next.
            logger.info(f"Song '{item.get('title')}' already exists in the queue, moving it to the front.")
            if existing.get('file_path') and not item.get('file_path'):
                item['file_path'] = existing['file_path']
            q._queue.remove(existing)
            q._queue.appendleft(item)
            return True

        # 2. Handle queue full scenarios
        if q.qsize() >= self.MAX_QUEUE_SIZE:
            # Search backwards from the end and delete the first bot-added song
            bot_song_removed = False
            for i in range(len(q._queue) - 1, -1, -1):
                if q._queue[i].get('added_by') == self.bot.user.id:
                    del q._queue[i]
                    bot_song_removed = True
                    logger.info("Queue is full; removed one bot-added song for priority song.")
                    break
            
            if not bot_song_removed:
                logger.info(f"Queue is full and no bot songs to remove (guild_id: {guild_id}). Cannot add song.")
                return False

        # 3. Add song to the front of the queue (use appendleft for efficiency)
        q._queue.appendleft(item)

        # 4. Rebuilding queue is no longer necessary
        return True

    async def get_next_item(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get the next item from the queue."""
        q = self.get_queue(guild_id)
        if q.empty():
            return None
        return await q.get()

    async def enforce_autoplay_limit(self, guild_id: int, limit: int = 5):
        """Ensure the number of autoplayed songs in the queue does not exceed the specified limit."""
        q = self.get_queue(guild_id)
        queue_list = list(q._queue)
        
        autoplay_songs_indices = [i for i, song in enumerate(queue_list) if song.get('added_by') == self.bot.user.id]
        
        if len(autoplay_songs_indices) > limit:
            # Calculate number of songs to remove
            to_remove_count = len(autoplay_songs_indices) - limit
            
            # Get indices of songs to remove (starting from the head)
            indices_to_remove = set(autoplay_songs_indices[:to_remove_count])
            
            # Filter out songs that need to be removed
            new_queue_list = [song for i, song in enumerate(queue_list) if i not in indices_to_remove]

            # Rebuild queue
            new_queue = asyncio.Queue()
            for song in new_queue_list:
                await new_queue.put(song)
            self.guild_queues[guild_id] = new_queue
            logger.info(f"Removed {to_remove_count} redundant autoplay songs from queue (guild_id: {guild_id}).")
