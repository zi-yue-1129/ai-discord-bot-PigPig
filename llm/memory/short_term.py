from typing import List, Any, Dict, Optional
import re
from collections import OrderedDict

import discord
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from function import func


def _speaker_label(author: Any, is_own_message: bool) -> str:
    """Names the author of a message the way the model should see them.

    The bot's own label stays its plain username. Everyone else gets the name people call them
    in the server (display name) next to the username, and other bots are marked ``BOT`` so
    their words are never taken for the bot's own.

    Args:
        author: The Discord author of the message.
        is_own_message: Whether this bot wrote the message.

    Returns:
        The label placed before ``| UserID:`` in the history prefix.
    """
    if is_own_message:
        return author.name
    display_name = getattr(author, "display_name", None) or author.name
    label = author.name if display_name == author.name else f"{display_name} ({author.name})"
    return f"BOT {label}" if author.bot else label


class ShortTermMemoryProvider:
    """
    Provides short-term memory as a list of LangChain messages.

    The provider fetches recent message history from the channel and converts
    each Discord message to a LangChain HumanMessage or AIMessage.
    """

    def __init__(self, bot: Any, limit: int = 10, max_cache_size: int = 100):
        """
        Initialize the provider.

        Args:
            limit: maximum number of recent messages to fetch from channel.
            max_cache_size: Maximum number of attachment results to retain in the cache.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if not isinstance(max_cache_size, int) or max_cache_size < 0:
            raise ValueError("max_cache_size must be a non-negative integer")
        self.limit = limit
        self.max_cache_size = max_cache_size
        self.bot = bot
        self._attachment_cache: OrderedDict = OrderedDict()

    async def get(self, message: discord.Message) -> List[BaseMessage]:
        """
        Fetch recent messages and return as LangChain BaseMessage list.

        The returned order is oldest -> newest.
        """
        try:
            from llm.utils.attachment_processor import is_processing_failure, process_attachment
            from llm.utils.embed_processor import process_embed
            from addons.settings import attachment_config as _att_cfg

            history = [
                msg async for msg in message.channel.history(limit=self.limit)
            ]
            history.reverse()

            # Pre-fetch all attachments concurrently
            attachment_tasks = []
            task_mapping = []  # To map task index back to (msg.id, att.id)
            attachment_results_by_msg = {}

            if _att_cfg.enabled:
                for msg in history:
                    if msg.attachments:
                        for att in msg.attachments:
                            # Check cache first
                            if att.id in self._attachment_cache:
                                # Move to end to mark as recently used
                                res = self._attachment_cache.pop(att.id)
                                self._attachment_cache[att.id] = res
                                attachment_results_by_msg.setdefault(msg.id, []).extend(res)
                            else:
                                attachment_tasks.append(process_attachment(att))
                                task_mapping.append((msg.id, att.id))

            if attachment_tasks:
                import asyncio
                results = await asyncio.gather(*attachment_tasks, return_exceptions=True)
                for (msg_id, att_id), res in zip(task_mapping, results):
                    if not isinstance(res, Exception) and isinstance(res, list):
                        attachment_results_by_msg.setdefault(msg_id, []).extend(res)

                        # Transient failures are not cached so they are retried next time.
                        if is_processing_failure(res):
                            continue
                        self._attachment_cache[att_id] = res
                        if len(self._attachment_cache) > self.max_cache_size:
                            self._attachment_cache.popitem(last=False)
                    else:
                        # Fallback or log error could go here if process_attachment didn't handle it
                        pass

            result: List[BaseMessage] = []
            for msg in history:
                content_parts = []
                content_suffix = []

                is_own_message = msg.author.id == self.bot.user.id
                content_prefix = f"{_speaker_label(msg.author, is_own_message)} | UserID:{msg.author.id} | MessageID:{msg.id}"

                # Include reactions
                if msg.reactions:
                    reactions_info = ", ".join(str(r.emoji) for r in msg.reactions)
                    content_suffix.append(f"reactions: {reactions_info}")
                # Include reference info if it's a reply
                if msg.reference:
                    ref_text = f"reply_to: {msg.reference.message_id}"
                    ref_msg = None
                    if hasattr(msg.reference, "resolved") and isinstance(msg.reference.resolved, discord.Message):
                        ref_msg = msg.reference.resolved
                    elif hasattr(msg.reference, "cached_message") and msg.reference.cached_message:
                        ref_msg = msg.reference.cached_message

                    if ref_msg:
                        ref_author = ref_msg.author.name
                        # Create a brief summary of the referenced content
                        ref_content = ref_msg.content.replace('\n', ' ')[:50]
                        if len(ref_msg.content) > 50:
                            ref_content += "..."
                        if not ref_content and ref_msg.attachments:
                            ref_content = "[Image/Attachment]"
                        ref_text = f"Replying to @{ref_author}: '{ref_content}' (MessageID:{msg.reference.message_id})"
                        
                    content_suffix.append(ref_text)

                # Provide both Unix timestamp and human-readable time
                ts = msg.created_at.timestamp()
                human_time = msg.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                content_suffix.append(f"timestamp: {ts} ({human_time})")

                # The bot's own past messages keep the identity prefix (its MessageID is a
                # valid target for reactions and replies) but get no trailing metadata:
                # models imitate that suffix and leak it into new replies.
                suffix = "" if is_own_message else f" [{' | '.join(content_suffix)}]"
                cleaned_content = ""
                if msg.content:
                    cleaned_content = re.sub(rf'<@!?{self.bot.user.id}>', '', msg.content).strip()
                body = f"<som> {cleaned_content} <eom>" if cleaned_content else "<som> <eom>"
                content_parts.append({"type": "text", "text": f"[{content_prefix}] {body}{suffix}"})

                if _att_cfg.enabled and msg.id in attachment_results_by_msg:
                    content_parts.extend(attachment_results_by_msg[msg.id])

                if msg.embeds and _att_cfg.embeds.enabled:
                    for embed in msg.embeds:
                        parts = process_embed(embed)
                        content_parts.extend(parts)

                # Only the bot's own messages are assistant turns. Other bots speak as
                # participants: as assistant turns the model would take their words as its own.
                if is_own_message:
                    result.append(AIMessage(content=content_parts))
                else:
                    # The name is only a hint: most chat templates drop it, so the speaker is
                    # also written into the text prefix above.
                    result.append(HumanMessage(
                        content=content_parts,
                        name=f"{msg.author.name}_{msg.author.id}"
                    ))

            return result
        except Exception as e:
            await func.report_error(e)
            return []
