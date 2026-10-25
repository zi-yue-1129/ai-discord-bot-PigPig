import discord
from discord.ext import commands
from discord import app_commands
import copy
import json
from dataclasses import dataclass
import os
import random
import time
from addons.logging import get_logger
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple, Union
from .language_manager import LanguageManager
from llm.relevance_judge import judge_relevance
from addons.tokens import tokens
from addons.settings import base_config
from function import func
import asyncio

# Module-level logger. Use "Bot" as default server_id for module-level events.
log = get_logger(server_id="Bot", source=__name__)

# Auto-response modes for a channel whose auto-response is on.
AUTO_RESPONSE_MODES = ("all", "chance", "relevant")
DEFAULT_AUTO_RESPONSE_CHANCE = 20


@dataclass(frozen=True)
class AutoResponseTuning:
    """Owner-set tuning for unprompted replies (``auto_response`` in base.yaml)."""

    # How long the bot counts as "in a conversation" with someone after replying to them.
    conversation_window_seconds: float = 180
    # In "relevant" mode, a channel's messages are judged by the model at most this often,
    # so a busy channel does not cost one model call per message.
    relevance_cooldown_seconds: float = 15
    # Messages shorter than this (after trimming) are never sent to the model.
    relevance_min_chars: int = 4
    # How many recent messages the model reads.
    relevance_history_messages: int = 8

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]]) -> "AutoResponseTuning":
        config = config or {}
        defaults = cls()
        values = {}
        for field_name in ("conversation_window_seconds", "relevance_cooldown_seconds",
                           "relevance_min_chars", "relevance_history_messages"):
            default = getattr(defaults, field_name)
            try:
                value = type(default)(config.get(field_name, default))
            except (TypeError, ValueError):
                log.warning(f"auto_response.{field_name} in base.yaml is not a number; using {default}")
                value = default
            values[field_name] = max(value, 0)
        values["relevance_history_messages"] = max(values["relevance_history_messages"], 1)
        return cls(**values)


def get_auto_response_settings(config: Dict[str, Any], channel_id: str) -> Dict[str, Any]:
    """Returns the channel's auto-response mode, chance (%) and keywords; mode is "off" when disabled."""
    if not config.get("auto_response", {}).get(channel_id, False):
        return {"mode": "off", "chance": 0, "keywords": []}
    raw = config.get("auto_response_settings", {}).get(channel_id) or {}
    mode = raw.get("mode", "all")
    if mode not in AUTO_RESPONSE_MODES:
        mode = "all"
    try:
        chance = int(raw.get("chance", DEFAULT_AUTO_RESPONSE_CHANCE))
    except (TypeError, ValueError):
        chance = DEFAULT_AUTO_RESPONSE_CHANCE
    keywords = [str(k).strip() for k in raw.get("keywords", []) if str(k).strip()]
    return {"mode": mode, "chance": max(0, min(chance, 100)), "keywords": keywords}


def decide_auto_response(
    settings: Dict[str, Any],
    content: str,
    bot_names: List[str],
    in_conversation: bool,
    roll: Optional[float] = None,
) -> bool:
    """Whether an unprompted message in an auto-response channel gets a reply.

    - all: every message.
    - chance: each message with probability ``chance`` percent.
    - relevant: messages that name the bot or one of the channel's keywords,
      or that come from someone the bot was just talking with. Anything else in
      this mode is left to the model (see ``ChannelManager.should_auto_respond``).
    """
    mode = settings.get("mode", "off")
    if mode == "all":
        return True
    if mode == "chance":
        roll = random.random() if roll is None else roll
        return roll * 100 < settings.get("chance", 0)
    if mode == "relevant":
        if in_conversation:
            return True
        text = (content or "").casefold()
        terms = [n for n in bot_names if n] + list(settings.get("keywords", []))
        return any(term.casefold() in text for term in terms)
    return False


class ChannelManager(commands.Cog):
    """Cog for managing server-wide and channel-specific response modes and permissions."""

    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/channel_configs"
        self.lang_manager: Optional[LanguageManager] = None
        self.tokens = tokens
        # guild_id -> (file mtime, config); re-read only when the file changes (the dashboard writes it too).
        self._config_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        # (channel_id, user_id) -> when the bot last replied to that user there.
        self._last_reply_at: Dict[Tuple[int, int], float] = {}
        # channel_id -> when the model last judged a message there ("relevant" mode).
        self._last_judged_at: Dict[int, float] = {}
        self.tuning = AutoResponseTuning.from_config(getattr(base_config, "auto_response", None))
        os.makedirs(self.data_dir, exist_ok=True)

    async def cog_load(self):
        """Initialize LanguageManager when the cog is loaded."""
        self.lang_manager = LanguageManager.get_instance(self.bot)

    def get_config_path(self, guild_id: str) -> str:
        """Get the file path for a guild's configuration."""
        return os.path.join(self.data_dir, f"{guild_id}.json")

    def load_config(self, guild_id: str) -> Dict[str, Any]:
        """Load configuration for a specific guild (cached until the file changes)."""
        config_path = self.get_config_path(guild_id)
        try:
            mtime = os.path.getmtime(config_path)
        except OSError:
            self._config_cache.pop(guild_id, None)
            return self._get_default_config()

        cached = self._config_cache.get(guild_id)
        if cached and cached[0] == mtime:
            return copy.deepcopy(cached[1])

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            return self._get_default_config()
        # Ensure necessary keys exist
        config.setdefault("auto_response", {})
        config.setdefault("auto_response_settings", {})
        config.setdefault("channel_modes", {})
        config.setdefault("mode", "unrestricted")
        self._config_cache[guild_id] = (mtime, config)
        return copy.deepcopy(config)

    def _get_default_config(self) -> Dict[str, Any]:
        """Provide a default configuration template."""
        return {
            "mode": "unrestricted", # Server-wide mode
            "whitelist": [],
            "blacklist": [],
            "auto_response": {},
            "auto_response_settings": {},  # channel_id -> {"mode", "chance", "keywords"}
            "channel_modes": {} # Per-channel mode overrides
        }

    def save_config(self, guild_id: str, config: Dict[str, Any]):
        """Save configuration for a specific guild."""
        config_path = self.get_config_path(guild_id)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self._config_cache[guild_id] = (os.path.getmtime(config_path), copy.deepcopy(config))
        except Exception as e:
            # Report it, then let the command fail instead of telling the user the setting was saved.
            asyncio.create_task(func.report_error(e, f"saving config for guild {guild_id}"))
            raise

    async def check_admin_permissions(self, interaction: discord.Interaction, *, defer: bool = False) -> bool:
        """Check if the user has administrator permissions or is the bot owner."""
        if defer and not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        
        bot_owner_id = getattr(self.tokens, 'bot_owner_id', 0)
        if interaction.user.guild_permissions.administrator or interaction.user.id == bot_owner_id:
            return True
        
        if self.lang_manager:
            error_message = self.lang_manager.translate(
                str(interaction.guild_id),
                "errors",
                "permission_denied"
            )
        else:
            error_message = "You do not have permission to perform this action. Restricted to administrators."
        
        if interaction.response.is_done():
            await interaction.edit_original_response(content=error_message)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
        return False

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="set_server_mode", description="Set the server-wide response mode (Whitelist/Blacklist)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Unrestricted", value="unrestricted"),
        app_commands.Choice(name="Whitelist", value="whitelist"),
        app_commands.Choice(name="Blacklist", value="blacklist")
    ])
    async def set_server_mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        """Set the global response mode for the entire server."""
        if not await self.check_admin_permissions(interaction, defer=True):
            return
            
        guild_id = str(interaction.guild_id)
        config = self.load_config(guild_id)
        config["mode"] = mode.value
        self.save_config(guild_id, config)
        
        if self.lang_manager:
            mode_name = self.lang_manager.translate(
                guild_id, "commands", "channel_manager", "set_server_mode", "choices", mode.value
            )
            response = self.lang_manager.translate(
                guild_id, "commands", "channel_manager", "set_server_mode", "responses", "success", mode=mode_name
            )
        else:
            response = f"Set **Server-wide** response mode to: {mode.name}"

        await interaction.edit_original_response(content=response)

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="set_channel_mode", description="Set a special mode for a specific channel (e.g., Story Mode)")
    @app_commands.describe(channel="The channel to set", mode="The mode to set for this channel")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Default (Follow Server Settings)", value="default"),
        app_commands.Choice(name="Story Mode", value="story")
    ])
    async def set_channel_mode(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread], mode: app_commands.Choice[str]):
        """Configure a specific mode override for a single channel."""
        if not await self.check_admin_permissions(interaction, defer=True):
            return

        guild_id = str(interaction.guild_id)
        config = self.load_config(guild_id)
        channel_id = str(channel.id)

        if mode.value == "default":
            if channel_id in config["channel_modes"]:
                del config["channel_modes"][channel_id]
                if self.lang_manager:
                    message = self.lang_manager.translate(
                        guild_id, "commands", "channel_manager", "set_channel_mode", "responses", "reset", channel=channel.mention
                    )
                else:
                    message = f"Reset mode for {channel.mention} to default."
            else:
                if self.lang_manager:
                    message = self.lang_manager.translate(
                        guild_id, "commands", "channel_manager", "set_channel_mode", "responses", "already_default", channel=channel.mention
                    )
                else:
                    message = f"{channel.mention} is already using default mode."
        else:
            config["channel_modes"][channel_id] = mode.value
            if self.lang_manager:
                mode_name = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "set_channel_mode", "choices", mode.value
                )
                message = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "set_channel_mode", "responses", "success", channel=channel.mention, mode=mode_name
                )
            else:
                message = f"Set mode for {channel.mention} to: **{mode.name}**."

        self.save_config(guild_id, config)
        await interaction.edit_original_response(content=message)

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="add_channel", description="Add channel to whitelist or blacklist")
    @app_commands.choices(list_type=[
        app_commands.Choice(name="Whitelist", value="whitelist"),
        app_commands.Choice(name="Blacklist", value="blacklist")
    ])
    async def add_channel_command(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread], list_type: app_commands.Choice[str]):
        """Add a channel to the server's whitelist or blacklist."""
        if not await self.check_admin_permissions(interaction, defer=True):
            return
            
        guild_id = str(interaction.guild_id)
        config = self.load_config(guild_id)
        channel_id = str(channel.id)
        
        if self.lang_manager:
            list_type_name = self.lang_manager.translate(
                guild_id, "commands", "channel_manager", "add_channel", "choices", list_type.value
            )
        else:
            list_type_name = list_type.name
        
        if channel_id not in config[list_type.value]:
            config[list_type.value].append(channel_id)
            self.save_config(guild_id, config)
            
            if self.lang_manager:
                success_message = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "add_channel", "responses", "success", channel=f"<#{channel_id}>", list_type=list_type_name
                )
            else:
                success_message = f"Added <#{channel_id}> to {list_type_name}"
            
            await interaction.edit_original_response(content=success_message)
        else:
            if self.lang_manager:
                exists_message = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "add_channel", "responses", "already_exists", channel=f"<#{channel_id}>", list_type=list_type_name
                )
            else:
                exists_message = f"<#{channel_id}> already exists in {list_type_name}"
            
            await interaction.edit_original_response(content=exists_message)

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="remove_channel", description="Remove channel from whitelist or blacklist")
    @app_commands.choices(list_type=[
        app_commands.Choice(name="Whitelist", value="whitelist"),
        app_commands.Choice(name="Blacklist", value="blacklist")
    ])
    async def remove_channel_command(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread], list_type: app_commands.Choice[str]):
        """Remove a channel from the server's whitelist or blacklist."""
        if not await self.check_admin_permissions(interaction, defer=True):
            return
            
        guild_id = str(interaction.guild_id)
        config = self.load_config(guild_id)
        channel_id = str(channel.id)
        
        if self.lang_manager:
            list_type_name = self.lang_manager.translate(
                guild_id, "commands", "channel_manager", "remove_channel", "choices", list_type.value
            )
        else:
            list_type_name = list_type.name
        
        if channel_id in config[list_type.value]:
            config[list_type.value].remove(channel_id)
            self.save_config(guild_id, config)
            
            if self.lang_manager:
                success_message = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "remove_channel", "responses", "success", channel=f"<#{channel_id}>", list_type=list_type_name
                )
            else:
                success_message = f"Removed <#{channel_id}> from {list_type_name}"
            
            await interaction.edit_original_response(content=success_message)
        else:
            if self.lang_manager:
                not_found_message = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "remove_channel", "responses", "not_found", channel=f"<#{channel_id}>", list_type=list_type_name
                )
            else:
                not_found_message = f"<#{channel_id}> does not exist in {list_type_name}"
            
            await interaction.edit_original_response(content=not_found_message)

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="auto_response", description="Set channel auto-response")
    @app_commands.describe(
        channel="The channel to set",
        mode="Off, reply to every message, reply by chance, or reply only when the topic is relevant",
        chance="For the chance mode: the percent of messages that get a reply (1-100)",
        keywords="For the relevant mode: extra comma-separated words that count as relevant",
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Every message", value="all"),
        app_commands.Choice(name="By chance", value="chance"),
        app_commands.Choice(name="Only when relevant", value="relevant"),
    ])
    async def auto_response_command(
        self,
        interaction: discord.Interaction,
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread],
        mode: app_commands.Choice[str],
        chance: Optional[app_commands.Range[int, 1, 100]] = None,
        keywords: Optional[str] = None,
    ):
        """Set how the bot replies, unprompted, to messages in a channel."""
        if not await self.check_admin_permissions(interaction, defer=True):
            return

        guild_id = str(interaction.guild_id)
        config = self.load_config(guild_id)
        channel_id = str(channel.id)
        config["auto_response"][channel_id] = mode.value != "off"
        if mode.value == "off":
            config["auto_response_settings"].pop(channel_id, None)
        else:
            previous = config["auto_response_settings"].get(channel_id, {})
            settings = {"mode": mode.value}
            if mode.value == "chance":
                settings["chance"] = chance or previous.get("chance", DEFAULT_AUTO_RESPONSE_CHANCE)
            if mode.value == "relevant":
                if keywords is not None:
                    settings["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
                else:
                    settings["keywords"] = previous.get("keywords", [])
            config["auto_response_settings"][channel_id] = settings
        self.save_config(guild_id, config)

        effective = get_auto_response_settings(config, channel_id)
        if self.lang_manager:
            mode_name = self.lang_manager.translate(
                guild_id, "commands", "channel_manager", "auto_response", "choices", mode.value
            )
            detail = ""
            if effective["mode"] == "chance":
                detail = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "auto_response", "details", "chance", chance=effective["chance"]
                )
            elif effective["mode"] == "relevant" and effective["keywords"]:
                detail = self.lang_manager.translate(
                    guild_id, "commands", "channel_manager", "auto_response", "details", "keywords", keywords=", ".join(effective["keywords"])
                )
            success_message = self.lang_manager.translate(
                guild_id, "commands", "channel_manager", "auto_response", "responses", "success", channel=f"<#{channel_id}>", enabled=mode_name
            ) + (f"\n{detail}" if detail else "")
        else:
            success_message = f"Set auto-response for <#{channel_id}> to: {mode.name}"

        await interaction.edit_original_response(content=success_message)

    def record_bot_reply(self, channel_id: int, user_id: int) -> None:
        """Remember that the bot just replied to this user in this channel."""
        now = time.monotonic()
        self._last_reply_at[(int(channel_id), int(user_id))] = now
        if len(self._last_reply_at) > 5000:
            cutoff = now - self.tuning.conversation_window_seconds
            self._last_reply_at = {k: t for k, t in self._last_reply_at.items() if t >= cutoff}

    async def should_auto_respond(self, message: discord.Message, guild_id: str) -> bool:
        """Whether an unprompted message in this channel gets a reply under its auto-response mode.

        In "relevant" mode the cheap rules come first; when none matches, a small model reads
        the recent conversation and decides (at most once per channel every
        ``relevance_cooldown_seconds``; see ``AutoResponseTuning``).
        """
        settings = get_auto_response_settings(self.load_config(guild_id), str(message.channel.id))
        if settings["mode"] == "off":
            return False
        now = time.monotonic()
        last = self._last_reply_at.get((message.channel.id, message.author.id))
        in_conversation = last is not None and now - last < self.tuning.conversation_window_seconds
        me = message.guild.me if message.guild else None
        bot_names = [getattr(self.bot.user, "name", ""), getattr(me, "display_name", "")]
        if decide_auto_response(settings, message.content, bot_names, in_conversation):
            return True
        if settings["mode"] != "relevant" or len((message.content or "").strip()) < self.tuning.relevance_min_chars:
            return False
        if now - self._last_judged_at.get(message.channel.id, float("-inf")) < self.tuning.relevance_cooldown_seconds:
            return False
        orchestrator = getattr(self.bot, "orchestrator", None)
        if orchestrator is None:
            return False
        self._last_judged_at[message.channel.id] = now
        try:
            return await judge_relevance(
                orchestrator, self.bot, message, settings["keywords"],
                history_messages=self.tuning.relevance_history_messages,
            )
        except Exception as e:
            await func.report_error(e, "auto-response relevance check")
            return False

    def is_allowed_channel(self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread], guild_id: str) -> Tuple[bool, bool, Optional[str]]:
        """
        Determine if the bot is allowed to respond in a channel and get its effective mode.

        Returns:
            A tuple of (is_allowed, auto_response_enabled, effective_mode).
        """
        config = self.load_config(guild_id)
        channel_id = str(channel.id)
        auto_response_enabled = config.get("auto_response", {}).get(channel_id, False)

        # 1. Check for a channel-specific mode override
        channel_mode = config.get("channel_modes", {}).get(channel_id)
        if channel_mode: # e.g., 'story'
            return True, auto_response_enabled, channel_mode

        # 2. If no override, use the server-wide mode
        server_mode = config.get("mode", "unrestricted")
        if server_mode == "unrestricted":
            return True, auto_response_enabled, server_mode
        elif server_mode == "whitelist":
            is_allowed = channel_id in config.get("whitelist", [])
            return is_allowed, auto_response_enabled, server_mode
        elif server_mode == "blacklist":
            is_allowed = channel_id not in config.get("blacklist", [])
            return is_allowed, auto_response_enabled, server_mode
            
        return False, False, server_mode


async def setup(bot):
    """Set up the ChannelManager cog."""
    await bot.add_cog(ChannelManager(bot))
