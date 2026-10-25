"""Decision wheel: ``/wheel spin`` picks one of the options typed, ``/wheel food`` one of the nearby restaurants.

The pick is made up front; the message is then edited a few times so it looks like the wheel
turns before it stops. ``/wheel food`` takes its options from the same recommender and
restaurant search as ``/search type:eat`` and ends on that restaurant's card.
"""

from __future__ import annotations

import asyncio
from typing import Any, List, Optional, Set

import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from addons.rate_limiter import format_wait
from function import func

from .eat.embeds import eatEmbed
from .eat.views import EatDetailView
from .games_lib import wheel
from .language_manager import LanguageManager

FRAME_SECONDS = 0.8
FOOD_OPTIONS = 6


class WheelCog(commands.Cog):
    """Spins a wheel of options; one spin per channel at a time."""

    group = app_commands.Group(name="wheel", description="Spin a wheel to decide", guild_only=True)

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="wheel")
        self.frame_seconds = FRAME_SECONDS
        self._spinning: Set[int] = set()

    async def cog_load(self) -> None:
        self.lang_manager = LanguageManager.get_instance(self.bot)

    def _t(self, guild_id: Any, key: str, **kwargs: Any) -> str:
        if self.lang_manager is None:
            return key
        return self.lang_manager.translate(str(guild_id), "commands", "wheel", "responses", key, **kwargs)

    async def _spin(self, interaction: discord.Interaction, title: str, options: List[str]) -> int:
        """Shows the spin on the (deferred) response and returns the picked index."""
        frames = wheel.spin(options)
        for position, pointer in enumerate(frames):
            final = position == len(frames) - 1
            embed = discord.Embed(
                title=title,
                description=wheel.render(options, pointer, final),
                colour=discord.Colour.gold() if final else discord.Colour.blurple(),
            )
            if final:
                embed.set_footer(text=self._t(interaction.guild_id, "result", option=options[pointer]))
            await interaction.edit_original_response(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            if not final:
                await asyncio.sleep(self.frame_seconds)
        return frames[-1]

    def _claim(self, interaction: discord.Interaction) -> bool:
        if interaction.channel_id in self._spinning:
            return False
        self._spinning.add(interaction.channel_id)
        return True

    @group.command(name="spin", description="Pick one of your options at random")
    @app_commands.describe(options="Options separated by commas, e.g. hot pot, ramen, curry")
    async def spin(self, interaction: discord.Interaction, options: str) -> None:
        guild_id = interaction.guild_id
        choices = wheel.parse_options(options)
        if len(choices) < wheel.MIN_OPTIONS:
            await interaction.response.send_message(self._t(guild_id, "too_few", minimum=wheel.MIN_OPTIONS), ephemeral=True)
            return
        if not self._claim(interaction):
            await interaction.response.send_message(self._t(guild_id, "busy"), ephemeral=True)
            return
        try:
            await interaction.response.defer()
            await self._spin(interaction, self._t(guild_id, "title", user=interaction.user.display_name), choices)
        finally:
            self._spinning.discard(interaction.channel_id)

    @group.command(name="food", description="Spin a wheel of nearby restaurants")
    @app_commands.describe(keyword="What kind of food (empty = the bot suggests one)")
    async def food(self, interaction: discord.Interaction, keyword: Optional[str] = None) -> None:
        guild_id = interaction.guild_id
        search = self.bot.get_cog("InternetSearchCog")
        if search is None or not all(hasattr(search, name) for name in ("db", "recommender", "provider")):
            await interaction.response.send_message(self._t(guild_id, "food_unavailable"), ephemeral=True)
            return
        # A restaurant search calls a paid API, so it counts like a chat message.
        limiter = getattr(self.bot, "rate_limiter", None)
        retry_after = limiter.hit("chat", interaction.user.id) if limiter else 0
        if retry_after:
            await interaction.response.send_message(self._t(guild_id, "rate_limited", seconds=format_wait(retry_after)), ephemeral=True)
            return
        if not self._claim(interaction):
            await interaction.response.send_message(self._t(guild_id, "busy"), ephemeral=True)
            return
        try:
            await interaction.response.defer()
            await self._food(interaction, search, (keyword or "").strip()[:50])
        except Exception as error:
            await func.report_error(error, "wheel food")
            await interaction.edit_original_response(content=self._t(guild_id, "food_failed"), embed=None)
        finally:
            self._spinning.discard(interaction.channel_id)

    async def _food(self, interaction: discord.Interaction, search: Any, keyword: str) -> None:
        guild_key = str(interaction.guild_id)
        if not keyword:
            keywords = [row[0] for row in search.db.getKeywords() or []]
            if not keywords:
                await interaction.edit_original_response(
                    content=self._t(guild_key, "food_none", keyword="?"), allowed_mentions=discord.AllowedMentions.none()
                )
                return
            keyword = search.recommender.suggest_keyword(guild_key, keywords)
        lang = self.lang_manager.get_server_lang(guild_key) if self.lang_manager else "en_US"
        provider = search.provider
        if hasattr(provider, "async_search_list"):
            results = await provider.async_search_list(keyword, lang=lang)
        else:
            results = await provider.search(keyword, lang=lang)
        ranked = (search.recommender.rank_candidates(guild_key, results or []) or results or [])[:FOOD_OPTIONS]
        ranked = [place for place in ranked if place.get("name")]
        if len(ranked) < wheel.MIN_OPTIONS:
            await interaction.edit_original_response(
                content=self._t(guild_key, "food_none", keyword=keyword), allowed_mentions=discord.AllowedMentions.none()
            )
            return
        names = [place["name"][: wheel.MAX_OPTION_LENGTH] for place in ranked]
        pick = await self._spin(interaction, self._t(guild_key, "food_title", keyword=keyword), names)
        place = ranked[pick]
        if not place.get("is_detailed") and hasattr(provider, "async_fetch_detail") and place.get("maps_url"):
            detail = await provider.async_fetch_detail(place["maps_url"], lang=lang)
            if detail:
                place.update(detail)
                place["is_detailed"] = True
        record_id = search.db.storeSearchRecord(
            discord_id=guild_key,
            title=place.get("name", ""),
            keyword=keyword,
            map_rate=str(place.get("rating", "")),
            tag=place.get("category", ""),
            map_address=place.get("address", ""),
        )
        view = EatDetailView(
            result=place,
            db=search.db,
            record_id=record_id,
            discord_id=guild_key,
            provider=provider,
            keyword=keyword,
            browse_results=ranked,
            browse_index=pick,
            lang_manager=self.lang_manager,
            guild_id=guild_key,
        )
        embed = eatEmbed(
            keyword=keyword,
            title=place.get("name", ""),
            address=place.get("address", ""),
            rating=place.get("rating", 0),
            photo_url=place.get("photo_url", ""),
            price_level=place.get("price_level", 0),
            opening_hours=place.get("opening_hours", []),
            lang_manager=self.lang_manager,
            guild_id=guild_key,
        )
        await interaction.edit_original_response(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WheelCog(bot))
