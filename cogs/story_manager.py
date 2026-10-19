import discord
from discord.ext import commands
from discord import app_commands
from addons.logging import get_logger
from typing import Any, Optional

from .story.manager import StoryManager
from .story.ui import UIManager
from .system_prompt.manager import SystemPromptManager
from function import func

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

    story = app_commands.Group(name="story", description="與故事模式相關的指令")

    @story.command(name="menu", description="🎭 開啟故事管理選單")
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

    @story.command(name="intervene", description="🎬 對故事走向進行干預")
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


async def setup(bot: commands.Bot):
    """
    設定函式，將 Cog 加入到 bot 中
    
    Args:
        bot: Discord Bot 實例
    """
    await bot.add_cog(StoryManagerCog(bot))