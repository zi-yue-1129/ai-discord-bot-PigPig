import discord
from discord.ext import commands
from addons.logging import get_logger
log = get_logger(source=__name__, server_id="system")
logger = log
import typing
from typing import Any, Optional

if typing.TYPE_CHECKING:
    from ..manager import StoryManager

from .views import InitialStoryView, ActiveStoryView
from .modals import CharacterCreateModal
from cogs.system_prompt.manager import SystemPromptManager


class UIManager:
    """
    故事模組的 UI 管理器
    
    負責協調和管理所有 UI 介面的顯示、更新與生命週期。
    採用臨時性 (ephemeral) 介面設計，降低狀態管理複雜度。
    """
    
    def __init__(self, bot: commands.Bot, story_manager: "StoryManager", system_prompt_manager: SystemPromptManager):
        self.bot = bot
        self.story_manager = story_manager
        self.character_db = story_manager.character_db
        self.system_prompt_manager = system_prompt_manager
        self.logger = log

    def _t(self, guild_id: Optional[int], *path: str, **kwargs: Any) -> str:
        """Translates a story UI string for the given guild.

        Args:
            guild_id: Guild whose language is used. May be None in DMs.
            *path: Translation key path, e.g. ``"story", "menu", "initial_title"``.
            **kwargs: Format arguments for the translated text.

        Returns:
            The translated text.
        """
        return self.story_manager.language_manager.translate(str(guild_id), *path, **kwargs)

    async def show_main_menu(self, interaction: discord.Interaction):
        """
        顯示主要的故事管理選單
        
        根據當前頻道是否有活躍的故事實例，決定顯示：
        1. InitialStoryView - 故事開始前的準備介面
        2. ActiveStoryView - 正在進行故事的管理介面
        
        Args:
            interaction: Discord 互動物件
        """
        try:
            # 檢查頻道權限
            channel_manager = self.bot.get_cog('ChannelManager')
            if not channel_manager:
                await interaction.response.send_message(
                    self._t(interaction.guild_id, "story", "menu", "channel_manager_missing"),
                    ephemeral=True
                )
                return
            
            # 檢查當前頻道是否有活躍的故事實例
            db = self.story_manager._get_db(interaction.guild_id)
            self.logger.info(f"[DEBUG] show_main_menu 調用 db.initialize() - Guild: {interaction.guild_id}")
            db.initialize()
            
            story_instance = db.get_story_instance(interaction.channel_id)
            has_active_story = story_instance and story_instance.is_active
            
            if has_active_story:
                # 顯示正在進行故事的管理介面
                view = ActiveStoryView(manager=self.story_manager, story_instance=story_instance)
                embed = self._create_active_story_embed(story_instance, interaction.guild_id)
                await interaction.response.send_message(
                    embed=embed, 
                    view=view, 
                    ephemeral=True
                )
            else:
                # 顯示故事開始前的準備介面
                view = InitialStoryView(manager=self.story_manager, channel_id=interaction.channel_id, guild_id=interaction.guild_id, ui_manager=self)
                
                # 動態載入世界選單選項
                await self._update_world_select_options(view, interaction.guild_id)
                
                embed = await self._create_initial_story_embed(interaction.guild_id, interaction.channel_id)
                await interaction.response.send_message(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )
                
        except Exception as e:
            self.logger.error(f"顯示主選單時發生錯誤: {e}", exc_info=True)
            error_message = self._t(interaction.guild_id, "story", "menu", "menu_load_error")
            
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
    
    async def _create_initial_story_embed(self, guild_id: int, channel_id: int) -> discord.Embed:
        """創建初始故事選單的 Embed"""
        embed = discord.Embed(
            title=self._t(guild_id, "story", "menu", "initial_title"),
            description=self._t(guild_id, "story", "menu", "initial_description"),
            color=discord.Color.blue()
        )
        
        # 檢查是否有可用的世界
        db = self.story_manager._get_db(guild_id)
        worlds = db.get_all_worlds()
        
        if worlds:
            world_list = "\n".join([f"• **{world.world_name}**" for world in worlds[:5]])
            if len(worlds) > 5:
                world_list += self._t(guild_id, "story", "menu", "more_worlds", count=len(worlds) - 5)
            embed.add_field(
                name=self._t(guild_id, "story", "menu", "available_worlds"),
                value=world_list,
                inline=False
            )
        else:
            embed.add_field(
                name=self._t(guild_id, "story", "menu", "available_worlds"),
                value=self._t(guild_id, "story", "menu", "no_worlds"),
                inline=False
            )
        
        embed.set_footer(text=self._t(guild_id, "story", "menu", "initial_footer"))
        return embed
    
    def _create_active_story_embed(self, story_instance, guild_id: Optional[int]) -> discord.Embed:
        """創建進行中故事的 Embed"""
        embed = discord.Embed(
            title=self._t(guild_id, "story", "menu", "active_title"),
            description=self._t(guild_id, "story", "menu", "active_description", world_name=story_instance.world_name),
            color=discord.Color.green()
        )
        
        # 顯示故事狀態
        if story_instance.is_active:
            status_text = self._t(guild_id, "story", "menu", "status_active")
        else:
            status_text = self._t(guild_id, "story", "menu", "status_paused")
        embed.add_field(name=self._t(guild_id, "story", "menu", "status_field"), value=status_text, inline=True)
        
        # 顯示參與角色數量
        char_count = len(story_instance.active_character_ids)
        embed.add_field(
            name=self._t(guild_id, "story", "menu", "participants_field"),
            value=self._t(guild_id, "story", "menu", "participants_count", count=char_count),
            inline=True
        )
        
        # 顯示最近事件
        if story_instance.event_log:
            recent_event = story_instance.event_log[-1]
            if len(recent_event) > 100:
                recent_event = recent_event[:100] + "..."
            embed.add_field(name=self._t(guild_id, "story", "menu", "recent_event_field"), value=recent_event, inline=False)
        
        embed.set_footer(text=self._t(guild_id, "story", "menu", "active_footer"))
        return embed
    
    async def _update_world_select_options(self, view, guild_id: int):
        """更新視圖中的世界選擇選單選項"""
        try:
            db = self.story_manager._get_db(guild_id)
            self.logger.info(f"[DEBUG] _update_world_select_options 調用 db.initialize() - Guild: {guild_id}")
            db.initialize()
            worlds = db.get_all_worlds()
            
            # 找到世界選擇組件並更新選項
            for item in view.children:
                if isinstance(item, discord.ui.Select):
                    options = []
                    if worlds:
                        for world in worlds[:25]:  # Discord 限制最多 25 個選項
                            options.append(discord.SelectOption(
                                label=world.world_name,
                                value=world.world_name,
                                description=world.attributes.get(
                                    'description', self._t(guild_id, "story", "menu", "no_description")
                                )[:100]
                            ))
                    else:
                        options.append(discord.SelectOption(
                            label=self._t(guild_id, "story", "menu", "no_worlds_option"),
                            value="none",
                            description=self._t(guild_id, "story", "menu", "no_worlds_option_description")
                        ))
                    
                    item.options = options
                    break
                    
        except Exception as e:
            self.logger.error(f"更新世界選單選項錯誤: {e}", exc_info=True)

    async def handle_load_default_character(self, interaction: discord.Interaction):
        """處理從頻道預設設定載入角色的請求"""
        try:
            if not interaction.guild_id or not interaction.channel_id:
                # 在私訊等情境下可能沒有 guild_id，直接返回
                await interaction.response.send_message(
                    self._t(interaction.guild_id, "story", "menu", "not_available_here"), ephemeral=True
                )
                return
            
            config = self.system_prompt_manager.get_channel_prompt_config(
                str(interaction.guild_id), str(interaction.channel_id)
            )

            if not config or "base_prompt" not in config:
                await interaction.response.send_message(
                    self._t(interaction.guild_id, "story", "menu", "no_default_character"),
                    ephemeral=True
                )
                return

            # 提取名稱和描述
            char_name = config.get("profile", {}).get("name") or config.get("name", "")
            char_description = config.get("base_prompt", "")

            await self.show_character_create_modal(
                interaction,
                name=char_name,
                description=char_description
            )

        except Exception as e:
            self.logger.error(f"載入預設角色時發生錯誤: {e}", exc_info=True)
            error_message = self._t(interaction.guild_id, "story", "menu", "default_load_error")
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)

    async def show_character_create_modal(self, interaction: discord.Interaction, name: str = "", description: str = ""):
        """顯示角色創建 Modal，可選填預設值"""
        modal = CharacterCreateModal(
            manager=self.story_manager,
            guild_id=interaction.guild_id,
            name=name,
            description=description
        )
        await interaction.response.send_modal(modal)