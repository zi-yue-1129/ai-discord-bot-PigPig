"""StatsCog: real-time user statistics tracking and historical log migration.

Records prefix and application command attempts in the dashboard statistics
database. Listens for on_message events to update per-user stats in the
user_stats table, and migrates historical NDJSON logs in the background.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

from addons.logging import get_logger
from cogs.memory.db.stats_storage import StatsStorage
from function import func, ROOT_DIR

logger = get_logger(server_id="system", source=__name__)


class StatsCog(commands.Cog):
    """Real-time user stats tracking and historical log migration.

    Attributes:
        bot: The Discord bot instance.
        stats_storage: StatsStorage instance for DB operations.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize StatsCog.

        Obtains a DatabaseConnection from the bot's procedural_storage
        and creates a StatsStorage instance.

        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
        self.stats_storage: Optional[StatsStorage] = None
        self._migration_task: Optional[asyncio.Task] = None

        # Obtain DB connection from procedural_storage (same DB as users table)
        procedural_storage = getattr(bot, "procedural_storage", None)
        if procedural_storage:
            db_conn = getattr(procedural_storage, "db", None)
            if db_conn:
                self.stats_storage = StatsStorage(db_conn)
                logger.info("StatsStorage initialized from procedural_storage.")
            else:
                logger.warning(
                    "procedural_storage has no 'db' attribute; "
                    "StatsCog will not track cumulative user stats."
                )
        else:
            logger.warning(
                "Bot has no procedural_storage; StatsCog will not track cumulative user stats."
            )

    async def cog_load(self) -> None:
        """Start background log migration task when cog loads."""
        if self.stats_storage:
            self._migration_task = asyncio.create_task(
                self._migrate_logs_background()
            )
            logger.info("Background log migration task scheduled.")

    async def cog_unload(self) -> None:
        """Cancel background migration task on cog unload."""
        if self._migration_task and not self._migration_task.done():
            self._migration_task.cancel()
            logger.info("Background log migration task cancelled.")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        """Record prefix command attempts before checks or execution finish.

        Args:
            ctx: Invocation context. Hybrid slash invocations are recorded by
                on_interaction instead. Guild ID ``0`` denotes direct messages.
        """
        if ctx.interaction is not None or ctx.command is None:
            return
        await self.bot.stats_collector.record_command(
            guild_id=str(ctx.guild.id) if ctx.guild else "0",
            user_id=str(ctx.author.id),
            command_name=ctx.command.qualified_name,
            timestamp=ctx.message.created_at.timestamp(),
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """Record application command attempts, including failed invocations.

        Args:
            interaction: Incoming Discord interaction. Autocomplete and UI
                interactions are excluded. Guild ID ``0`` denotes direct messages.
        """
        if interaction.type != discord.InteractionType.application_command:
            return
        command = interaction.command
        if command is not None:
            command_name = command.qualified_name
        else:
            # Resolve subcommands even before the command tree caches its command.
            data = interaction.data
            if data is None:
                raise ValueError("Application command interaction has no data")
            command_names = [data["name"]]
            options = data.get("options", [])
            while options:
                subcommand = next(
                    (option for option in options if option["type"] in (1, 2)),
                    None,
                )
                if subcommand is None:
                    break
                command_names.append(subcommand["name"])
                options = subcommand.get("options", [])
            command_name = " ".join(command_names)
        await self.bot.stats_collector.record_command(
            guild_id=str(interaction.guild_id) if interaction.guild_id else "0",
            user_id=str(interaction.user.id), command_name=command_name,
            timestamp=interaction.created_at.timestamp(),
        )

    # ------------------------------------------------------------------
    # Real-time on_message listener
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        """Update user stats for every incoming message.

        Args:
            message: The Discord message object.
        """
        # Skip bot messages and DMs
        if not message.guild or message.author.bot:
            return
        if not self.stats_storage:
            return

        try:
            user_id = str(message.author.id)
            guild_id = str(message.guild.id)
            channel_name = getattr(message.channel, "name", "unknown")
            timestamp = (
                message.created_at.isoformat()
                if message.created_at
                else datetime.now(timezone.utc).isoformat()
            )
            content = message.content or ""

            # 1) Update cumulative stats in procedural.db
            await asyncio.shield(
                self.stats_storage.upsert_user_stats(
                    user_id=user_id,
                    guild_id=guild_id,
                    message_content=content,
                    channel_id=str(message.channel.id),
                    timestamp=timestamp,
                )
            )

            # 2) Update event stats in stats.db for dashboard trends
            if hasattr(self.bot, "stats_collector"):
                await self.bot.stats_collector.record_message(
                    guild_id=guild_id,
                    user_id=user_id,
                    channel_id=str(message.channel.id)
                )

        except Exception as e:
            # Stats are non-critical: log and continue so message handling is unaffected
            logger.error(
                "StatsCog on_message stats update failed: %s", e, exc_info=True
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Counts a reaction on a guild member's message (bots and self-reactions excluded).

        Args:
            payload: The raw reaction event (works for messages outside the cache).
        """
        if not self.stats_storage or payload.guild_id is None:
            return
        author_id = payload.message_author_id
        if author_id is None or author_id == payload.user_id:
            return
        if (payload.member is not None and payload.member.bot) or self._is_bot(payload.guild_id, author_id):
            return
        await self.stats_storage.record_reaction(
            message_id=str(payload.message_id),
            guild_id=str(payload.guild_id),
            channel_id=str(payload.channel_id),
            author_id=str(author_id),
            created_at=discord.utils.snowflake_time(payload.message_id).timestamp(),
            delta=1,
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        """Takes a removed reaction off a counted message's total.

        Args:
            payload: The raw reaction event; it carries no message author, so only a
                message already counted is updated.
        """
        if not self.stats_storage or payload.guild_id is None:
            return
        reactor = self._member(payload.guild_id, payload.user_id)
        if reactor is not None and reactor.bot:
            return
        await self.stats_storage.record_reaction(
            message_id=str(payload.message_id),
            guild_id=str(payload.guild_id),
            channel_id=str(payload.channel_id),
            author_id=None,
            created_at=discord.utils.snowflake_time(payload.message_id).timestamp(),
            delta=-1,
            reactor_id=str(payload.user_id),
        )

    def _member(self, guild_id: int, user_id: int) -> Optional[discord.Member]:
        """Returns a cached guild member, or None when the guild or member is not cached."""
        guild = self.bot.get_guild(guild_id) if hasattr(self.bot, "get_guild") else None
        return guild.get_member(user_id) if guild is not None else None

    def _is_bot(self, guild_id: int, user_id: int) -> bool:
        """Returns whether a cached member is a bot (unknown members count as people)."""
        member = self._member(guild_id, user_id)
        return member is not None and member.bot

    # ------------------------------------------------------------------
    # Background historical log migration
    # ------------------------------------------------------------------

    async def _migrate_logs_background(self) -> None:
        """Ingest historical NDJSON log files into user_stats and stats.db.

        Processes logs/{guild_id}/{YYYYMMDD}/info.jsonl files that have
        not been processed yet (tracked via log_migration_state table).
        """
        if not self.stats_storage:
            return

        # Wait for bot to be fully ready before starting migration
        await self.bot.wait_until_ready()
        
        # Ensure StatsCollector is initialized
        if hasattr(self.bot, "stats_collector"):
            await self.bot.stats_collector.initialize()

        # Small initial delay to avoid competing with startup I/O
        await asyncio.sleep(10)
        await self.stats_storage.prune_activity_history()

        logs_root = Path(ROOT_DIR) / "logs"
        if not logs_root.is_dir():
            logger.info("No logs/ directory found; skipping migration.")
            return

        logger.info("Starting background log migration from %s", logs_root)

        try:
            # Find all guild_id directories (numeric names only)
            guild_dirs = sorted(
                d for d in logs_root.iterdir()
                if d.is_dir() and d.name.isdigit()
            )

            live_since = await self.stats_storage.get_or_init_live_since(
                datetime.now(timezone.utc).strftime("%Y%m%d")
            )
            for guild_dir in guild_dirs:
                guild_id = guild_dir.name
                try:
                    await self._migrate_guild_logs(guild_id, guild_dir, live_since)
                except asyncio.CancelledError:
                    logger.info("Migration cancelled for guild %s", guild_id)
                    return
                except Exception as e:
                    logger.error(
                        "Migration failed for guild %s: %s", guild_id, e
                    )
                    await func.report_error(
                        e, f"Log migration failed for guild {guild_id}"
                    )
                    continue

            logger.info("Background log migration completed for all guilds.")
            # Imported old logs may have added weeks that are already past the kept window.
            await self.stats_storage.prune_activity_history()
        except asyncio.CancelledError:
            logger.info("Background log migration task was cancelled.")
        except Exception as e:
            logger.error("Background log migration encountered error: %s", e)
            await func.report_error(e, "Background log migration failed")

    async def _migrate_guild_logs(
        self, guild_id: str, guild_dir: Path, live_since: str
    ) -> None:
        """Migrate log files for a single guild.

        Args:
            guild_id: The guild's Discord snowflake ID.
            guild_dir: Path to the guild's log directory.
            live_since: First log day (``YYYYMMDD``) already counted live by
                ``on_message``; it and later days are never imported.
        """
        # Get last processed date
        last_processed = await self.stats_storage.get_migration_state(guild_id)

        # Find date directories (YYYYMMDD format)
        date_dirs = sorted(
            d for d in guild_dir.iterdir()
            if d.is_dir() and len(d.name) == 8 and d.name.isdigit()
        )

        if not date_dirs:
            return

        processed_count = 0

        for date_dir in date_dirs:
            date_str = date_dir.name

            # Skip already-processed dates and days counted live
            if last_processed and date_str <= last_processed:
                continue
            if date_str >= live_since:
                continue

            jsonl_path = date_dir / "info.jsonl"
            if not jsonl_path.is_file():
                continue

            logger.info(
                "Migrating logs for guild=%s date=%s", guild_id, date_str
            )

            batch_count = 0
            batch_cumulative = []
            batch_events = []
            
            try:
                with open(jsonl_path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Only process actual user messages
                        if record.get("action") != "receive_message":
                            continue

                        user_id = record.get("user_id", "")
                        if not user_id:
                            continue

                        channel_name = record.get("channel_or_file", "unknown")
                        channel_id = str(record.get("extra", {}).get("channel_id", "0"))
                        timestamp_str = record.get(
                            "timestamp",
                            datetime.now(timezone.utc).isoformat(),
                        )
                        content = record.get("message", "")

                        # Cumulative stats record
                        batch_cumulative.append({
                            "user_id": user_id,
                            "guild_id": guild_id,
                            "message_content": content,
                            "channel_id": channel_id,
                            "timestamp": timestamp_str,
                        })

                        # Event stats record (for trends)
                        try:
                            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            ts_float = dt.timestamp()
                        except Exception:
                            ts_float = time.time()
                        
                        batch_events.append((guild_id, user_id, channel_id, ts_float))

                        batch_count += 1
                        processed_count += 1

                        # Yield event loop every 500 records
                        if len(batch_cumulative) >= 500:
                            await self.stats_storage.bulk_upsert_user_stats(batch_cumulative)
                            if hasattr(self.bot, "stats_collector"):
                                await self.bot.stats_collector.bulk_record_messages(batch_events)
                            
                            batch_cumulative.clear()
                            batch_events.clear()
                            await asyncio.sleep(0)

                    # Process any remaining records
                    if batch_cumulative:
                        await self.stats_storage.bulk_upsert_user_stats(batch_cumulative)
                        if hasattr(self.bot, "stats_collector"):
                            await self.bot.stats_collector.bulk_record_messages(batch_events)

            except Exception as e:
                logger.error("Error reading %s: %s", jsonl_path, e)
                await func.report_error(e, f"Log migration read error: {jsonl_path}")
                continue

            # Mark this date as processed
            await self.stats_storage.set_migration_state(guild_id, date_str)
            logger.info(
                "Completed migration for guild=%s date=%s (%d records)",
                guild_id,
                date_str,
                batch_count,
            )

            # Sleep between days to avoid I/O contention
            await asyncio.sleep(30)

        if processed_count > 0:
            logger.info(
                "Guild %s migration complete: %d total records processed.",
                guild_id,
                processed_count,
            )


async def setup(bot: commands.Bot) -> None:
    """Register StatsCog with the bot."""
    await bot.add_cog(StatsCog(bot))
