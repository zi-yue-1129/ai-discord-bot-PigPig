import discord
from discord.ext import commands
from addons.logging import get_logger
log = get_logger(server_id="system", source=__name__)
logger = log
import typing
from typing import Optional

if typing.TYPE_CHECKING:
    from ..manager import StoryManager

from ..models import StoryWorld, StoryCharacter, StoryInstance, Location


class WorldCreateModal(discord.ui.Modal):
    """
    世界創建 Modal
    
    提供表單介面讓使用者輸入新世界的名稱、背景和第一個地點的資訊
    """
    
    def __init__(self, manager: "StoryManager", guild_id: int):
        super().__init__(title="🌍 創建新的故事世界")
        self.story_manager = manager
        self.story_db = manager._get_db(guild_id)
        self.guild_id = guild_id
        self.logger = log

    world_name = discord.ui.TextInput(
        label="世界名稱",
        placeholder="輸入你的世界名稱（例如：中土世界、賽博朋克 2077）",
        max_length=50,
        required=True
    )

    background = discord.ui.TextInput(
        label="世界背景",
        placeholder="描述這個世界的背景故事、設定和特色...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )

    first_location_name = discord.ui.TextInput(
        label="初始地點名稱",
        placeholder="為你的世界設定第一個地點（例如：起始的村莊）",
        max_length=50,
        required=True
    )

    location_description = discord.ui.TextInput(
        label="地點描述",
        placeholder="描述這個地點的環境、特色...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """處理世界創建表單提交"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            self.story_db.initialize()

            # 檢查世界名稱是否已存在
            existing_world = self.story_db.get_world(self.world_name.value)
            if existing_world:
                await interaction.followup.send(
                    f"❌ 名為 `{self.world_name.value}` 的世界已經存在。請選擇其他名稱。",
                    ephemeral=True
                )
                return
            
            # 創建初始地點
            initial_location = Location(
                name=self.first_location_name.value,
                attributes={'description': self.location_description.value}
            )
            
            # 創建新世界，設定背景並將初始地點加入
            new_world = StoryWorld(
                guild_id=self.guild_id,
                world_name=self.world_name.value,
                attributes={'background': self.background.value},
                locations=[initial_location]
            )
            
            self.story_db.save_world(new_world)
            
            # 成功回應
            embed = discord.Embed(
                title="✅ 世界創建成功！",
                description=f"**{self.world_name.value}** 已成功創建。",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🌍 世界名稱",
                value=self.world_name.value,
                inline=False
            )
            embed.add_field(
                name="📖 背景故事",
                value=self.background.value[:500] + ("..." if len(self.background.value) > 500 else ""),
                inline=False
            )
            embed.add_field(
                name="📍 初始地點",
                value=f"**{self.first_location_name.value}**: {self.location_description.value[:400]}...",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"創建世界時發生錯誤: {e}", exc_info=True)
            await func.report_error(e)
            await interaction.followup.send(
                "❌ 創建世界時發生錯誤，請稍後再試。",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """處理 Modal 錯誤"""
        self.logger.error(f"WorldCreateModal 錯誤: {error}", exc_info=True)
        await func.report_error(error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 處理請求時發生錯誤",
                    ephemeral=True
                )
        except:
            pass


class CharacterCreateModal(discord.ui.Modal):
    """
    角色創建 Modal
    
    提供表單介面讓使用者創建新角色
    """
    
    def __init__(self, manager: "StoryManager", guild_id: int, name: str = "", description: str = ""):
        super().__init__(title="👤 創建新角色")
        self.story_manager = manager
        self.character_db = manager.character_db
        self.guild_id = guild_id
        self.logger = log

        self.character_name = discord.ui.TextInput(
            label="角色名稱",
            placeholder="輸入你的角色名稱",
            max_length=50,
            required=True,
            default=name
        )
        
        self.description = discord.ui.TextInput(
            label="角色描述",
            placeholder="描述角色的外觀、背景、性格等...",
            style=discord.TextStyle.paragraph,
            max_length=800,
            required=True,
            default=description
        )

        self.webhook_url = discord.ui.TextInput(
            label="角色 Webhook 網址 (選填)",
            placeholder="請貼上 Discord Webhook 的 URL...",
            required=False,
            style=discord.TextStyle.short
        )

        self.privacy_input = discord.ui.TextInput(
            label="是否公開此角色？(預設為是)",
            placeholder="請輸入 '是' 或 '否'...",
            required=False,
            default="是"
        )
        
        self.add_item(self.character_name)
        self.add_item(self.description)
        self.add_item(self.webhook_url)
        self.add_item(self.privacy_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """處理角色創建表單提交"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            self.character_db.initialize()

            # 獲取創作者 ID 和公開狀態
            creator_id = interaction.user.id
            is_public = self.privacy_input.value.strip().lower() != '否'

            # 創建新角色
            new_character = StoryCharacter(
                guild_id=self.guild_id,
                name=self.character_name.value,
                description=self.description.value,
                webhook_url=self.webhook_url.value or None,
                is_pc=True,  # 玩家角色
                user_id=creator_id, # 創建者即為第一個使用者
                creator_id=creator_id,
                is_public=is_public
            )
            
            self.character_db.save_character(new_character)
            
            # 成功回應
            embed = discord.Embed(
                title="✅ 角色創建成功！",
                description=f"**{self.character_name.value}** 已成功創建。",
                color=discord.Color.green()
            )
            embed.add_field(
                name="👤 角色名稱",
                value=self.character_name.value,
                inline=True
            )
            embed.add_field(
                name="🏢 所屬伺服器",
                value=interaction.guild.name,
                inline=True
            )
            embed.add_field(
                name="📝 角色描述",
                value=self.description.value[:300] + ("..." if len(self.description.value) > 300 else ""),
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"創建角色時發生錯誤: {e}", exc_info=True)
            await func.report_error(e)
            await interaction.followup.send(
                "❌ 創建角色時發生錯誤，請稍後再試。",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """處理 Modal 錯誤"""
        self.logger.error(f"CharacterCreateModal 錯誤: {error}", exc_info=True)
        await func.report_error(error)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 處理請求時發生錯誤",
                    ephemeral=True
                )
        except:
            pass


class StoryStartModal(discord.ui.Modal):
    """
    故事開始 Modal

    收集故事開始時的初始世界狀態
    """

    def __init__(self, story_manager: "StoryManager", bot: commands.Bot, guild_id: int, channel_id: int, world_name: str):
        super().__init__(title="🎬 設定故事初始狀態")
        self.story_manager = story_manager
        self.bot = bot
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.world_name = world_name
        self.logger = log

    initial_date = discord.ui.TextInput(
        label="初始日期 (選填)",
        placeholder="留空讓 AI 決定故事的開始日期",
        required=False
    )

    initial_time = discord.ui.TextInput(
        label="初始時間 (選填)",
        placeholder="留空讓 AI 決定故事的開始時間",
        required=False
    )

    initial_location = discord.ui.TextInput(
        label="初始地點",
        placeholder="例如：寧靜的森林小徑上",
        required=True,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """
        立即回應互動以防止超時，並在背景準備 NPC 選擇介面。
        """
        # 立即回應，告訴使用者我們正在處理
        await interaction.response.send_message("⏳ 正在準備 NPC 選擇介面，請稍候...", ephemeral=True)
        
        # 在背景執行耗時的操作
        self.bot.loop.create_task(self._prepare_and_send_npc_select(interaction))

    async def _prepare_and_send_npc_select(self, interaction: discord.Interaction):
        """
        在背景中執行耗時操作，然後發送帶有 NPC 選擇視圖的 followup 訊息。
        """
        try:
            self.logger.info(f"[DEBUG] _prepare_and_send_npc_select 開始 - world: {self.world_name}")
            self.logger.info(f"[DEBUG] 參數 - guild_id: {self.guild_id}, channel_id: {self.channel_id}")
            self.logger.info(f"[DEBUG] 初始狀態 - date: {self.initial_date.value}, time: {self.initial_time.value}, location: {self.initial_location.value}")

            # 獲取系統提示詞
            self.logger.info(f"[DEBUG] 開始獲取系統提示詞...")
            system_prompt_manager = self.story_manager.system_prompt_manager
            system_prompt_content = ""
            if system_prompt_manager:
                self.logger.info(f"[DEBUG] 找到 SystemPromptManager，準備獲取提示詞...")
                prompt_data = system_prompt_manager.get_effective_prompt(
                    str(self.channel_id), str(self.guild_id)
                )
                system_prompt_content = prompt_data.get('prompt', '')
                self.logger.info(f"[DEBUG] 系統提示詞獲取成功 - length: {len(system_prompt_content)}")
            else:
                self.logger.warning("[DEBUG] SystemPromptManager not found via StoryManager.")

            # 創建 NPC 選擇視圖 (這是耗時操作)
            self.logger.info(f"[DEBUG] 準備創建 NPCSelectView...")
            from ..ui.views import NPCSelectView
            self.logger.info(f"[DEBUG] NPCSelectView 導入成功，開始調用 create 方法...")
            
            # Use .value or None to ensure None is passed if the field is empty
            date_value = self.initial_date.value if self.initial_date.value else None
            time_value = self.initial_time.value if self.initial_time.value else None

            view = await NPCSelectView.create(
                manager=self.story_manager,
                interaction=interaction,
                channel_id=self.channel_id,
                world_name=self.world_name,
                initial_date=date_value,
                initial_time=time_value,
                initial_location=self.initial_location.value,
                system_prompt=system_prompt_content,
            )
            self.logger.info(f"[DEBUG] NPCSelectView 創建成功")
            
            # 使用 followup.send 發送最終的介面
            self.logger.info(f"[DEBUG] 準備發送 followup 訊息...")
            await interaction.followup.send(
                "請選擇要一同參與故事的 NPC：",
                view=view,
                ephemeral=True
            )
            self.logger.info(f"[DEBUG] followup 訊息發送成功")

        except Exception as e:
            self.logger.error(f"[DEBUG] 準備 NPC 選擇時發生錯誤: {e}", exc_info=True)
            await func.report_error(e)
            try:
                await interaction.followup.send(
                    "❌ 準備 NPC 選擇介面時發生錯誤，請稍後再試。",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"[DEBUG] 發送錯誤訊息也失敗: {followup_error}", exc_info=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """處理 Modal 錯誤"""
        self.logger.error(f"StoryStartModal 錯誤: {error}", exc_info=True)
        await func.report_error(error)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ 處理請求時發生錯誤", ephemeral=True)


class InterventionModal(discord.ui.Modal):
    """
    A modal for users to submit an OOC intervention to the story director.
    """

    def __init__(self, manager: "StoryManager"):
        super().__init__(title="🎬 故事干預指令")
        self.manager = manager
        self.logger = log

    intervention_text = discord.ui.TextInput(
        label="給導演的指示",
        placeholder="請輸入你希望故事接下來如何發展的指示...\n例如：讓天氣突然變壞，並安排一個神秘的陌生人登場。",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handles the submission of the intervention."""
        try:
            # Defer the response to avoid timeouts
            await interaction.response.defer(ephemeral=True)

            # Store the intervention text in the manager
            self.manager.interventions[interaction.channel_id] = self.intervention_text.value

            await interaction.followup.send(
                "✅ 你的干預指令已成功發送給導演。它將在下一次玩家發言後生效。",
                ephemeral=True
            )
            self.logger.info(f"Intervention submitted for channel {interaction.channel_id}: {self.intervention_text.value}")

        except Exception as e:
            self.logger.error(f"Error submitting intervention for channel {interaction.channel_id}: {e}", exc_info=True)
            await func.report_error(e)
            await interaction.followup.send(
                "❌ 發送干預指令時發生錯誤，請稍後再試。",
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Handles errors in the modal."""
        self.logger.error(f"InterventionModal error: {error}", exc_info=True)
        await func.report_error(error)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ 處理請求時發生錯誤。", ephemeral=True)