import asyncio
import re
import base64
import io
from datetime import date

import discord
from discord.ext import commands
from discord import app_commands
from addons.logging import get_logger
from addons.rate_limiter import format_wait
from addons.visibility import audience_can_read, can_read, current_member
from typing import Any, Dict, List, Optional

from llm.game_writer import QuotaExhausted
from llm.story_recap_writer import write_recap
from .story import dice
from .story.manager import StoryManager
from .story.recap_store import RecapStore
from .story.ui import UIManager
from .system_prompt.manager import SystemPromptManager
from function import func

RECAP_DB_PATH = "data/story_recaps.db"
# Messages read back for a recap.
RECAP_HISTORY = 40
_WEBHOOK_ID = re.compile(r"/webhooks/(\d+)/")
RECAP_LINE_CHARS = 400
EMBED_DESCRIPTION_LIMIT = 4000
CARD_DESCRIPTION_CHARS = 2000
CARD_FIELDS = 10
CARD_FIELD_NAME_CHARS = 50
CARD_FIELD_CHARS = 200
_LANGUAGE_NAMES = {"zh_TW": "Traditional Chinese", "zh_CN": "Simplified Chinese", "ja_JP": "Japanese", "en_US": "English"}

class StoryManagerCog(commands.Cog, name="StoryManagerCog"):
    """
    故事模組主要 Cog
    
    重構後的故事模組採用 UI 驅動設計：
    - 單一 /story 命令作為入口點
    - 所有功能透過 Discord UI 元件操作
    - 臨時性介面降低狀態管理複雜度
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger(server_id="Bot", source="story_manager")
        self.system_prompt_manager: Optional[SystemPromptManager] = None
        self.story_manager: Optional[StoryManager] = None
        self.ui_manager: Optional[UIManager] = None
        self.recap_store = RecapStore(RECAP_DB_PATH)
        # One daily recap check at a time per channel, so two quick messages post one recap.
        self._recap_locks: Dict[int, asyncio.Lock] = {}
        self._today = lambda: date.today().isoformat()
        self.logger.info("StoryManagerCog (UI版本) 已初始化")

    def _t(self, guild_id: Optional[int], *path: str, **kwargs: Any) -> str:
        """Translates a story UI string for the given guild.

        Args:
            guild_id: Guild whose language is used. May be None in DMs.
            *path: Translation key path, e.g. ``"story", "menu", "starting_up"``.
            **kwargs: Format arguments for the translated text.

        Returns:
            The translated text.

        Raises:
            RuntimeError: If the LanguageManager cog is not loaded.
        """
        language_manager = self.bot.get_cog("LanguageManager")
        if language_manager is None:
            raise RuntimeError("LanguageManager cog is not loaded; cannot translate story text")
        return language_manager.translate(str(guild_id), *path, **kwargs)

    story = app_commands.Group(name="story", description="Story mode commands")

    @story.command(name="menu", description="🎭 Open the story menu")
    async def story_menu(self, interaction: discord.Interaction):
        """
        故事管理主命令
        
        根據當前頻道狀態顯示對應的 UI 介面：
        - 無故事：顯示初始設定選單（創建世界、角色、開始故事）
        - 有故事：顯示故事控制面板（加入、暫停、結束等）
        """
        try:
            if not self.ui_manager:
                self.logger.warning("UIManager 未初始化，無法顯示選單。")
                await interaction.response.send_message(
                    self._t(interaction.guild_id, "story", "menu", "starting_up"), ephemeral=True
                )
                return
            await self.ui_manager.show_main_menu(interaction)
            
        except Exception as e:
            self.logger.error(f"故事選單錯誤: {e}", exc_info=True)
            await func.report_error(e)
            error_message = self._t(interaction.guild_id, "story", "menu", "menu_load_error")
            
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)

    @story.command(name="intervene", description="🎬 Steer where the story goes")
    async def intervene(self, interaction: discord.Interaction):
        """
        Allows a user to intervene in the story with OOC instructions for the director.
        """
        try:
            if not self.story_manager:
                self.logger.warning("StoryManager 未初始化，無法執行干預。")
                await interaction.response.send_message(
                    self._t(interaction.guild_id, "story", "menu", "starting_up"), ephemeral=True
                )
                return

            # Check if a story is active in this channel
            db = self.story_manager._get_db(interaction.guild_id)
            story_instance = db.get_story_instance(interaction.channel_id)

            if not story_instance or not story_instance.is_active:
                await interaction.response.send_message(
                    self._t(interaction.guild_id, "story", "menu", "intervene_no_active_story"),
                    ephemeral=True
                )
                return

            # Show the intervention modal
            from .story.ui.modals import InterventionModal
            modal = InterventionModal(self.story_manager, interaction.guild_id)
            await interaction.response.send_modal(modal)

        except Exception as e:
            self.logger.error(f"Error in /story intervene command: {e}", exc_info=True)
            await func.report_error(e)
            await interaction.response.send_message(
                self._t(interaction.guild_id, "story", "menu", "intervene_error"),
                ephemeral=True
            )

    # ------------------------------------------------------------------ dice
    def _active_story(self, guild_id: Optional[int], channel_id: Optional[int]) -> Any:
        """The channel's running story, or None."""
        if not self.story_manager or guild_id is None or channel_id is None:
            return None
        instance = self.story_manager._get_db(guild_id).get_story_instance(channel_id)
        return instance if instance and instance.is_active else None

    @app_commands.command(name="roll", description="Roll dice, e.g. 2d6+3 (in a story, the story follows the result)")
    @app_commands.describe(dice_notation="Dice to roll, e.g. d20, 2d6+3, 4d6-1", reason="What the roll is for (optional)")
    async def roll(
        self,
        interaction: discord.Interaction,
        dice_notation: app_commands.Range[str, 1, 60],
        reason: Optional[app_commands.Range[str, 1, 100]] = None,
    ) -> None:
        guild_id = interaction.guild_id
        try:
            result = dice.roll(dice_notation)
        except dice.DiceError as error:
            if error.key == "dice_too_many":
                text = self._t(guild_id, "story", "addons", "dice_too_many", max_dice=dice.MAX_DICE, max_sides=dice.MAX_SIDES)
            else:
                text = self._t(guild_id, "story", "addons", "dice_invalid")
            await interaction.response.send_message(text, ephemeral=True)
            return
        reason = " ".join(reason.split()) if reason else None
        text = self._t(guild_id, "story", "addons", "roll_result", user=interaction.user.mention, result=result.describe())
        if reason:
            text += "\n" + self._t(guild_id, "story", "addons", "roll_reason", reason=reason)
        in_story = self._active_story(guild_id, interaction.channel_id) is not None
        if in_story:
            text += "\n" + self._t(guild_id, "story", "addons", "roll_in_story")
        roll = None
        if in_story:
            note = f"{interaction.user.display_name} rolled {result.describe()}"
            if reason:
                note += f" for: {reason}"
            # Queued before the reply goes out: a story message right after the roll shows up must see it.
            # A turn starting meanwhile waits for the reply, and uses the roll only if it went out.
            roll = self.story_manager.add_dice_result(interaction.channel_id, note, delivered=False)
        try:
            await interaction.response.send_message(text, allowed_mentions=discord.AllowedMentions.none())
        except BaseException:
            # Nobody saw the roll: no turn may use it.
            if roll is not None:
                self.story_manager.discard_dice_result(interaction.channel_id, roll)
            raise
        if roll is not None:
            self.story_manager.confirm_dice_result(roll)

    # ----------------------------------------------------------------- recap
    async def _recap_text(self, channel: Any, instance: Any, user_id: Optional[int], before: Any = None) -> Optional[str]:
        """The recap of the story in ``channel``: written by the model, else the latest saved summary."""
        guild_id = instance.guild_id
        lines: List[str] = []
        bot_id = getattr(self.bot.user, "id", None)
        # Story characters speak through webhooks, in embeds like the bot's own story messages.
        webhook_ids = self._story_webhook_ids(instance)
        try:
            async for message in channel.history(limit=RECAP_HISTORY, before=before):
                from_story = message.author.id == bot_id or getattr(message, "webhook_id", None) in webhook_ids
                if from_story and message.embeds:
                    content = message.embeds[0].description or ""
                else:
                    content = message.content
                content = " ".join((content or "").split())[:RECAP_LINE_CHARS]
                if content:
                    lines.append(f"{message.author.display_name}: {content}")
        except discord.HTTPException:
            self.logger.warning(f"story recap: could not read channel {getattr(channel, 'id', None)}", exc_info=True)
        lines.reverse()
        orchestrator = getattr(self.bot, "orchestrator", None)
        text = None
        if orchestrator is not None and (lines or instance.summaries):
            limiter = getattr(self.bot, "rate_limiter", None)
            charge = (lambda: limiter.hit("chat", user_id)) if limiter is not None and user_id is not None else None
            language_manager = self.bot.get_cog("LanguageManager")
            lang = language_manager.get_server_lang(str(guild_id)) if language_manager else "en_US"
            try:
                text = await write_recap(
                    orchestrator, str(guild_id), _LANGUAGE_NAMES.get(lang, "English"), instance.summaries[-3:], lines, charge
                )
            except QuotaExhausted:
                text = None
        if not text and instance.summaries:
            text = instance.summaries[-1]
        return text.strip()[:EMBED_DESCRIPTION_LIMIT] if text else None

    def _story_webhook_ids(self, instance: Any) -> set:
        """The ids of the webhooks the story's characters speak through."""
        character_db = getattr(self.story_manager, "character_db", None)
        ids = set()
        for character_id in getattr(instance, "active_character_ids", None) or []:
            character = character_db.get_character(character_id) if character_db is not None else None
            found = _WEBHOOK_ID.search(getattr(character, "webhook_url", None) or "")
            if found:
                ids.add(int(found.group(1)))
        return ids

    def _recap_embed(self, guild_id: int, text: str) -> discord.Embed:
        return discord.Embed(
            title=self._t(guild_id, "story", "addons", "recap_title"),
            description=text,
            colour=discord.Colour.dark_teal(),
        )

    @story.command(name="recap", description="📜 Show a \"previously on…\" of this channel's story")
    async def recap(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        instance = self._active_story(guild_id, interaction.channel_id)
        if instance is None:
            await interaction.response.send_message(self._t(guild_id, "story", "addons", "no_story"), ephemeral=True)
            return
        # The recap retells the channel's history, so it is only for members who may read it, and
        # it is posted for the channel only when everyone who sees the channel may read the history.
        if not can_read(interaction.channel, interaction.user):
            await interaction.response.send_message(self._t(guild_id, "story", "addons", "recap_no_history"), ephemeral=True)
            return
        private = not audience_can_read(interaction.channel)
        await interaction.response.defer(ephemeral=private)
        text = await self._recap_text(interaction.channel, instance, interaction.user.id)
        # Checked again after the (slow) generation: permissions may have changed meanwhile, and the
        # interaction's member is a snapshot, so the member is looked up again.
        member = await current_member(interaction.guild, interaction.user.id)
        if not private and not audience_can_read(interaction.channel):
            # The public placeholder is replaced by a note; the recap itself goes only to the requester.
            await interaction.followup.send(self._t(guild_id, "story", "addons", "recap_sent_privately"))
            private = True
            member = await current_member(interaction.guild, interaction.user.id)
        # From here to the reply nothing is awaited, so both decisions still hold when it is sent:
        # who may see it (``private``, decided after the last await) and whether the requester may.
        if not can_read(interaction.channel, member):
            await interaction.followup.send(self._t(guild_id, "story", "addons", "recap_no_history"), ephemeral=True)
            return
        if not text:
            await interaction.followup.send(self._t(guild_id, "story", "addons", "recap_empty"), ephemeral=private)
            return
        await interaction.followup.send(
            embed=self._recap_embed(guild_id, text), ephemeral=private, allowed_mentions=discord.AllowedMentions.none()
        )

    async def maybe_post_daily_recap(self, message: discord.Message) -> None:
        """Before the first story message of a new day, posts a recap of the day the story last moved on."""
        guild_id, channel_id = message.guild.id, message.channel.id
        instance = self._active_story(guild_id, channel_id)
        if instance is None:
            return
        lock = self._recap_locks.setdefault(channel_id, asyncio.Lock())
        async with lock:
            today = self._today()
            last_day = self.recap_store.last_active_day(channel_id)
            if last_day == today:
                return
            try:
                # Posted for the whole channel: skipped where anyone who sees new messages may not read the history.
                if last_day is not None and audience_can_read(message.channel):
                    text = await self._recap_text(message.channel, instance, message.author.id, before=message)
                    # Checked again right before posting: permissions may have changed during the generation.
                    if text and audience_can_read(message.channel):
                        await message.channel.send(
                            embed=self._recap_embed(guild_id, text), allowed_mentions=discord.AllowedMentions.none()
                        )
            except Exception as error:
                # A recap is a courtesy: the story goes on without it and it is not tried again today.
                self.logger.warning(f"story recap: daily recap failed in channel {channel_id}", exc_info=True)
                await func.report_error(error, "story daily recap")
            finally:
                self.recap_store.set_active_day(channel_id, today)

    # ------------------------------------------------------------------ card
    async def _card_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        if not self.story_manager or interaction.guild_id is None:
            return []
        characters = self.story_manager.character_db.get_selectable_characters(interaction.guild_id, interaction.user.id)
        current = (current or "").casefold()
        return [
            app_commands.Choice(name=character.name[:100], value=character.character_id)
            for character in characters
            if current in character.name.casefold()
        ][:25]

    @story.command(name="card", description="🃏 Draw a character card picture (uses your image quota)")
    @app_commands.describe(character="The character to draw")
    @app_commands.autocomplete(character=_card_autocomplete)
    async def card(self, interaction: discord.Interaction, character: str) -> None:
        guild_id = interaction.guild_id
        if not self.story_manager:
            await interaction.response.send_message(self._t(guild_id, "story", "menu", "starting_up"), ephemeral=True)
            return
        found = self.story_manager.character_db.get_character(character)
        # Only characters the user may pick: public ones of this server, or their own.
        if (
            found is None
            or found.guild_id != guild_id
            or not (found.is_public or found.creator_id == interaction.user.id)
        ):
            await interaction.response.send_message(self._t(guild_id, "story", "addons", "card_not_found"), ephemeral=True)
            return
        images = self.bot.get_cog("ImageGenerationCog")
        if images is None or not hasattr(images, "_generate_image_logic"):
            await interaction.response.send_message(self._t(guild_id, "story", "addons", "card_unavailable"), ephemeral=True)
            return
        limiter = getattr(self.bot, "rate_limiter", None)
        use = None
        if limiter is None:
            retry_after = 0
        elif hasattr(limiter, "take"):
            retry_after, use = limiter.take("image", interaction.user.id)
        else:
            retry_after = limiter.hit("image", interaction.user.id)
        if retry_after:
            await interaction.response.send_message(
                self._t(guild_id, "story", "addons", "card_rate_limited", seconds=format_wait(retry_after)), ephemeral=True
            )
            return
        # A private character's card is shown only to its creator.
        private = not found.is_public
        attachment = None
        try:
            await interaction.response.defer(ephemeral=private)
        except BaseException:
            if use is not None:
                limiter.refund(use)
            raise
        # A history of its own, dropped afterwards: the card's details never reach the channel's
        # shared image history (other members' requests), nor does that history reach the card.
        history_key = f"story_card:{interaction.id}"
        try:
            result = await images._generate_image_logic(card_prompt(found), str(guild_id), history_key)
            attachment = next((item for item in result.get("attachments", []) if item.get("data_base64")), None)
        finally:
            history = getattr(images, "conversation_history", None)
            if isinstance(history, dict):
                history.pop(history_key, None)
            # No card, no charge.
            if attachment is None and use is not None:
                limiter.refund(use)
        if attachment is None:
            await interaction.followup.send(self._t(guild_id, "story", "addons", "card_failed"), ephemeral=True)
            return
        file = discord.File(io.BytesIO(base64.b64decode(attachment["data_base64"])), filename="character_card.png")
        embed = discord.Embed(
            title=found.name[:256],
            description=(found.description or "")[:CARD_DESCRIPTION_CHARS],
            colour=discord.Colour.purple(),
        )
        # An embed holds at most 6000 characters in all.
        for name, value in list((found.attributes or {}).items())[:CARD_FIELDS]:
            embed.add_field(name=str(name)[:CARD_FIELD_NAME_CHARS], value=str(value)[:CARD_FIELD_CHARS] or "—", inline=True)
        embed.set_image(url="attachment://character_card.png")
        await interaction.followup.send(
            embed=embed, file=file, ephemeral=private, allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Cog 準備就緒事件。
        此時所有 cogs 都已載入，可以安全地獲取其他 cog。
        """
        self.logger.info("StoryManagerCog 進入 on_ready 狀態，開始初始化依賴。")
        
        system_prompt_manager_cog = self.bot.get_cog("SystemPromptManagerCog")
        if system_prompt_manager_cog:
            self.system_prompt_manager = system_prompt_manager_cog.manager
            self.story_manager = StoryManager(self.bot, self, self.system_prompt_manager)
            self.ui_manager = UIManager(self.bot, self.story_manager, self.system_prompt_manager)
            
            await self.story_manager.initialize()
            self.logger.info("StoryManagerCog 已成功連接到 SystemPromptManagerCog 並完成初始化。")
        else:
            self.logger.error("警告：StoryManagerCog 在 on_ready 後仍無法找到 SystemPromptManagerCog。模組將無法正常運作。")

    async def handle_story_message(self, message: discord.Message):
        """
        處理故事頻道中的訊息
        
        此方法由 bot.py 的 on_message 事件呼叫，
        當頻道模式為 'story' 時處理使用者的故事互動。
        
        Args:
            message: Discord 訊息物件
        """
        if not self.story_manager:
            self.logger.warning("StoryManager 未初始化，跳過訊息處理")
            return
        
        try:
            await self.maybe_post_daily_recap(message)
            await self.story_manager.process_story_message(message)
            
        except Exception as e:
            self.logger.error(
                f"處理故事訊息時發生錯誤 (頻道 {message.channel.id}): {e}", 
                exc_info=True
            )
            await func.report_error(e)
            
            # 發送友善的錯誤訊息
            guild_id = message.guild.id if message.guild else None
            error_embed = discord.Embed(
                title=self._t(guild_id, "story", "menu", "story_interrupted_title"),
                description=self._t(guild_id, "story", "menu", "story_interrupted_description"),
                color=discord.Color.orange()
            )
            error_embed.set_footer(
                text=self._t(guild_id, "story", "menu", "error_details_footer", error=str(e)[:100])
            )
            
            try:
                await message.reply(embed=error_embed)
            except:
                # 如果無法回覆，嘗試發送到頻道
                try:
                    await message.channel.send(embed=error_embed)
                except:
                    # 最後的備用方案
                    await message.channel.send(self._t(guild_id, "story", "menu", "story_process_error"))


def card_prompt(character: Any) -> str:
    """The image prompt for a character card, from the character's saved details."""
    parts = [
        "A trading-card style character portrait illustration, no text or letters on the image.",
        f"Character: {character.name}.",
    ]
    if character.description:
        parts.append(f"Appearance and personality: {character.description[:800]}")
    attributes = ", ".join(f"{key}: {value}" for key, value in list((character.attributes or {}).items())[:10])
    if attributes:
        parts.append(f"Traits: {attributes[:400]}")
    return " ".join(parts)


async def setup(bot: commands.Bot):
    """
    設定函式，將 Cog 加入到 bot 中
    
    Args:
        bot: Discord Bot 實例
    """
    await bot.add_cog(StoryManagerCog(bot))