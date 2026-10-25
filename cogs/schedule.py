import discord
from discord import app_commands
from discord.ext import commands, tasks
import yaml
import re
from datetime import datetime, timedelta
import pytz
import os
from typing import Dict, List, Optional, Set, Tuple
from .language_manager import LanguageManager
from addons.logging import get_logger
from function import func
from addons.discord_text import reply_in_chunks

logger = get_logger(server_id="Bot", source="schedule")

SCHEDULE_TZ = pytz.timezone('Asia/Taipei')
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
DAY_CHOICES = [
    app_commands.Choice(name="Monday", value="monday"),
    app_commands.Choice(name="Tuesday", value="tuesday"),
    app_commands.Choice(name="Wednesday", value="wednesday"),
    app_commands.Choice(name="Thursday", value="thursday"),
    app_commands.Choice(name="Friday", value="friday"),
    app_commands.Choice(name="Saturday", value="saturday"),
    app_commands.Choice(name="Sunday", value="sunday"),
]
_TIME_RANGE = re.compile(r"^\s*([01]?\d|2[0-3]):([0-5]\d)\s*-\s*([01]?\d|2[0-3]):([0-5]\d)\s*$")


def normalize_time_range(text: str) -> Optional[str]:
    """Returns "HH:MM-HH:MM" for a valid time range, otherwise None."""
    match = _TIME_RANGE.match(text or "")
    if not match:
        return None
    h1, m1, h2, m2 = (int(g) for g in match.groups())
    return f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"


def events_starting_at(schedule: dict, moment: datetime) -> List[Tuple[str, str]]:
    """The (time range, description) of every event whose start is ``moment`` (same weekday, hour and minute)."""
    weekday = WEEKDAYS[moment.weekday()]
    found = []
    for day, events in (schedule or {}).items():
        if str(day).strip().casefold() != weekday or not isinstance(events, list):
            continue
        for event in events:
            if not isinstance(event, dict):
                continue
            time_range = normalize_time_range(str(event.get("time", "")))
            description = str(event.get("description") or "").strip()
            if not time_range or not description:
                continue
            if time_range[:5] == moment.strftime("%H:%M"):
                found.append((time_range, description))
    return found

class ScheduleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule_dir = "data/schedule"
        os.makedirs(self.schedule_dir, exist_ok=True)
        self.lang_manager: Optional[LanguageManager] = None
        # (user id, event start) already announced, so a restart or a slow tick does not repeat one.
        self._notified: Set[Tuple[int, str]] = set()

    async def cog_load(self):
        """當 Cog 載入時初始化語言管理器"""
        self.lang_manager = LanguageManager.get_instance(self.bot)
        self.notify_upcoming.start()

    async def cog_unload(self):
        self.notify_upcoming.cancel()

    def _load_user_schedule(self, user_id: int) -> Optional[dict]:
        filepath = os.path.join(self.schedule_dir, f"{user_id}.yaml")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _save_user_schedule(self, user_id: int, data: dict) -> None:
        with open(os.path.join(self.schedule_dir, f"{user_id}.yaml"), "w", encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)

    @tasks.loop(minutes=1)
    async def notify_upcoming(self):
        """Pings users whose schedule has an event starting in their chosen number of minutes."""
        now = datetime.now(SCHEDULE_TZ).replace(second=0, microsecond=0)
        for name in os.listdir(self.schedule_dir):
            if not name.endswith(".yaml") or not name[:-5].isdigit():
                continue
            user_id = int(name[:-5])
            try:
                data = self._load_user_schedule(user_id) or {}
                notify = data.get("notify") or {}
                if not isinstance(notify, dict) or not notify.get("enabled"):
                    continue
                lead = int(notify.get("minutes_before", 10))
                start = now + timedelta(minutes=lead)
                for time_range, description in events_starting_at(data.get("schedule", {}), start):
                    key = (user_id, start.strftime("%Y-%m-%d %H:%M"))
                    if key in self._notified:
                        continue
                    self._notified.add(key)
                    await self._send_event_notice(user_id, data.get("channel_id", 0), time_range, description, lead)
            except Exception as e:
                await func.report_error(e, f"schedule notify for user {user_id}")
        # Keep only today's keys.
        today = now.strftime("%Y-%m-%d")
        self._notified = {k for k in self._notified if k[1].startswith(today)}

    @notify_upcoming.before_loop
    async def _wait_until_ready(self):
        await self.bot.wait_until_ready()

    async def _send_event_notice(self, user_id: int, channel_id: int, time_range: str, description: str, lead: int):
        channel = self.bot.get_channel(channel_id) if channel_id else None
        guild_id = str(channel.guild.id) if channel is not None and getattr(channel, "guild", None) else "0"
        text = self.lang_manager.translate(
            guild_id, "commands", "schedule_notify", "notice",
            user=f"<@{user_id}>", minutes=lead, time=time_range, description=description,
        )
        allowed = discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(id=user_id)])
        if channel is not None:
            try:
                await channel.send(text, allowed_mentions=allowed)
                return
            except discord.HTTPException:
                logger.warning("schedule: could not post notice in channel %s", channel_id)
        user = self.bot.get_user(user_id)
        if user is not None:
            try:
                await user.send(text, allowed_mentions=allowed)
            except discord.HTTPException:
                logger.warning("schedule: could not DM notice to user %s", user_id)

    @app_commands.command(name="schedule_notify", description="Get pinged before each event in your schedule")
    @app_commands.describe(
        enabled="Turn the reminders on or off",
        minutes_before="How many minutes before each event (default 10)",
    )
    async def schedule_notify_command(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        minutes_before: Optional[app_commands.Range[int, 0, 120]] = None,
    ) -> None:
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        data = self._load_user_schedule(interaction.user.id)
        if data is None:
            await interaction.response.send_message(
                self.lang_manager.translate(guild_id, "commands", "query_schedule", "responses", "no_schedule"),
                ephemeral=True,
            )
            return
        data, _ = self._sanitize_schedule_data(data, interaction.channel_id)
        previous = data.get("notify") if isinstance(data.get("notify"), dict) else {}
        lead = minutes_before if minutes_before is not None else int(previous.get("minutes_before", 10))
        data["notify"] = {"enabled": enabled, "minutes_before": lead}
        # Notices go to the channel where the user last turned them on.
        if enabled and interaction.channel_id:
            data["channel_id"] = interaction.channel_id
        self._save_user_schedule(interaction.user.id, data)
        key = "enabled" if enabled else "disabled"
        await interaction.response.send_message(
            self.lang_manager.translate(guild_id, "commands", "schedule_notify", "responses", key, minutes=lead),
            ephemeral=True,
        )

    def _sanitize_schedule_data(self, data, fallback_channel_id: int):
        """Ensure schedule_data has required keys and types. Returns (data, repaired)."""
        repaired = False
        if not isinstance(data, dict):
            logger.warning("schedule_data was not a dict. Resetting to empty dict.")
            data = {}
            repaired = True
        if 'schedule' not in data or not isinstance(data.get('schedule'), dict):
            logger.warning("Missing or invalid 'schedule' key. Initializing to empty dict.")
            data['schedule'] = {}
            repaired = True
        if 'channel_id' not in data or not isinstance(data.get('channel_id'), int):
            logger.warning("Missing or invalid 'channel_id'. Using fallback_channel_id=%s", fallback_channel_id)
            data['channel_id'] = int(fallback_channel_id) if isinstance(fallback_channel_id, int) else 0
            repaired = True
        return data, repaired

    @app_commands.command(name="upload_schedule", description="Upload your schedule as a YAML file")
    async def upload_schedule_command(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(thinking=True)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        
        try:
            yaml_data = await file.read()
            await self._core_upload_schedule(interaction.user.id, interaction.channel_id, yaml_data)
            success_msg = self.lang_manager.translate(
                guild_id, "commands", "upload_schedule", "responses", "success"
            ) if self.lang_manager else "行程表已成功上傳！"
            await interaction.edit_original_response(content=success_msg)
        except Exception as e:
            await func.report_error(e, "uploading schedule")
            error_msg = self.lang_manager.translate(
                guild_id, "commands", "upload_schedule", "responses", "error", error=str(e)
            ) if self.lang_manager else f"上傳行程表時發生錯誤：{str(e)}"
            await interaction.edit_original_response(content=error_msg)

    async def _core_upload_schedule(self, user_id: int, channel_id: int, yaml_data: bytes):
        try:
            schedule = yaml.safe_load(yaml_data)
            if not isinstance(schedule, dict):
                raise yaml.YAMLError("YAML root must be a mapping.")
            schedule_data = {"channel_id": channel_id, "schedule": schedule}
            with open(os.path.join(self.schedule_dir, f"{user_id}.yaml"), "w", encoding='utf-8') as f:
                yaml.dump(schedule_data, f, allow_unicode=True)
        except yaml.YAMLError as e:
            error_msg = self.lang_manager.translate(
                "0", "system", "schedule", "errors", "yaml_parse_error", error=str(e)
            ) if self.lang_manager else f"YAML檔案解析錯誤：{str(e)}"
            raise Exception(error_msg)

    @app_commands.guild_only()
    @app_commands.command(name="query_schedule", description="Look up a schedule")
    @app_commands.choices(query_type=[
        app_commands.Choice(name="Full schedule", value="full"),
        app_commands.Choice(name="At a specific time", value="specific_time"),
        app_commands.Choice(name="Next event", value="next")
    ])
    @app_commands.choices(day=[
        app_commands.Choice(name="Monday", value="Monday"),
        app_commands.Choice(name="Tuesday", value="Tuesday"),
        app_commands.Choice(name="Wednesday", value="Wednesday"),
        app_commands.Choice(name="Thursday", value="Thursday"),
        app_commands.Choice(name="Friday", value="Friday"),
        app_commands.Choice(name="Saturday", value="Saturday"),
        app_commands.Choice(name="Sunday", value="Sunday")
    ])
    async def query_schedule_command(self, interaction: discord.Interaction, query_type: app_commands.Choice[str], time: str = None, day: app_commands.Choice[str] = None, target_user: discord.Member = None):
        await interaction.response.defer(thinking=True)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        
        try:
            target_user_id = target_user.id if target_user else interaction.user.id
            result = await self._core_query_schedule(interaction, query_type.value, target_user_id, time, day.value if day else None)
            await reply_in_chunks(interaction, result)
        except Exception as e:
            await func.report_error(e, "querying schedule")
            error_msg = self.lang_manager.translate(
                guild_id, "commands", "query_schedule", "responses", "error", error=str(e)
            ) if self.lang_manager else f"查詢行程表時發生錯誤：{str(e)}"
            await interaction.edit_original_response(content=error_msg)

    async def _core_query_schedule(self, interaction_or_ctx, query_type: str, target_user_id:int, time: str = None, day: str = None):
        guild_id = str(interaction_or_ctx.guild_id) if hasattr(interaction_or_ctx, 'guild_id') and interaction_or_ctx.guild_id else str(interaction_or_ctx.guild.id) if hasattr(interaction_or_ctx, 'guild') else "0"
        
        try:
            user_id = interaction_or_ctx.user.id if hasattr(interaction_or_ctx, 'user') else interaction_or_ctx.author.id
            channel_id = interaction_or_ctx.channel_id if hasattr(interaction_or_ctx, 'channel_id') else interaction_or_ctx.channel.id
        except AttributeError:
            return "Invalid interaction or context object."

        filepath = os.path.join(self.schedule_dir, f"{target_user_id}.yaml")
        if not os.path.exists(filepath):
            return self.lang_manager.translate(
                guild_id, "commands", "query_schedule", "responses", "no_schedule"
            ) if self.lang_manager else "找不到您的行程表。請使用 `/upload_schedule` 命令上傳行程表。"
        
        with open(filepath, "r", encoding='utf-8') as f:
            schedule_data = yaml.safe_load(f)
        if schedule_data is None:
            schedule_data = {}
        schedule_data, repaired = self._sanitize_schedule_data(schedule_data, channel_id)
        if repaired:
            with open(filepath, "w", encoding='utf-8') as fw:
                yaml.dump(schedule_data, fw, allow_unicode=True)

        guild = interaction_or_ctx.guild
        try:
            queried_user = await guild.fetch_member(target_user_id)
        except discord.NotFound:
            queried_user = None
        if queried_user is None:
            return self.lang_manager.translate(
                guild_id, "commands", "query_schedule", "responses", "user_not_found"
            ) if self.lang_manager else "找不到該使用者。"

        query_channel = guild.get_channel(channel_id)
        schedule_channel = guild.get_channel(schedule_data.get("channel_id", 0))

        if query_channel is None or schedule_channel is None:
            return self.lang_manager.translate(
                guild_id, "commands", "query_schedule", "responses", "channel_not_found"
            ) if self.lang_manager else "找不到頻道。"

        query_perms = query_channel.permissions_for(interaction_or_ctx.user)
        schedule_perms = schedule_channel.permissions_for(queried_user)

        if not query_perms.read_messages or not schedule_perms.read_messages:
            return self.lang_manager.translate(
                guild_id, "commands", "query_schedule", "responses", "permission_denied"
            ) if self.lang_manager else "您或被查詢者無權限查看此頻道。"

        schedule = schedule_data.get("schedule", {})
        tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(tz)

        if query_type == "full":
            return self.format_full_schedule(schedule, guild_id)
        elif query_type == "specific_time":
            try:
                specific_time = datetime.strptime(time if time else now.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
                return self.format_specific_time_schedule(schedule, specific_time, day, guild_id)
            except ValueError:
                return self.lang_manager.translate(
                    guild_id, "commands", "query_schedule", "responses", "invalid_time_format"
                ) if self.lang_manager else "無效的時間格式。請使用 YYYY-MM-DD HH:MM:SS 格式。"
        elif query_type == "next":
            return self.format_next_schedule(schedule, now, guild_id)
        else:
            return self.lang_manager.translate(
                guild_id, "commands", "query_schedule", "responses", "invalid_query_type"
            ) if self.lang_manager else "無效的查詢類型。"

    def format_full_schedule(self, schedule, guild_id="0"):
        title = self.lang_manager.translate(
            guild_id, "system", "schedule", "format", "full_schedule_title"
        ) if self.lang_manager else "**完整行程表:**"
        output = title + "\n"
        
        if not schedule:
            empty_msg = self.lang_manager.translate(
                guild_id, "system", "schedule", "format", "empty_schedule"
            ) if self.lang_manager else "行程表是空的。"
            return empty_msg
            
        time_column = self.lang_manager.translate(
            guild_id, "system", "schedule", "format", "time_column"
        ) if self.lang_manager else "時間"
        
        description_column = self.lang_manager.translate(
            guild_id, "system", "schedule", "format", "description_column"
        ) if self.lang_manager else "說明"
        
        no_events = self.lang_manager.translate(
            guild_id, "system", "schedule", "format", "no_events"
        ) if self.lang_manager else "沒有行程。"
        
        for day, events in schedule.items():
            # 嘗試翻譯星期名稱
            translated_day = self.lang_manager.translate(
                guild_id, "commands", "schedule", "query_schedule", "choices", "weekdays", day
            ) if self.lang_manager else day
            
            day_header = self.lang_manager.translate(
                guild_id, "system", "schedule", "format", "day_header", day=translated_day
            ) if self.lang_manager else f"**{translated_day}:**"
            output += day_header + "\n"
            
            if events:
                output += f"| {time_column} | {description_column} |\n"
                output += "|---|---| \n"
                for event in events:
                    time_str = event.get('time')
                    desc = event.get('description')
                    if time_str is None or desc is None:
                        logger.warning("Event missing keys: %s", event)
                        time_str = time_str if time_str is not None else "-"
                        desc = desc if desc is not None else "-"
                    output += f"| {time_str} | {desc} |\n"
            else:
                output += no_events + "\n"
        return output

    def format_specific_time_schedule(self, schedule, specific_time, day, guild_id="0"):
        title = self.lang_manager.translate(
            guild_id, "system", "schedule", "format", "specific_time_title",
            time=specific_time.strftime('%Y-%m-%d %H:%M:%S')
        ) if self.lang_manager else f"**{specific_time.strftime('%Y-%m-%d %H:%M:%S')} 的行程:**"
        output = title + "\n"
        found = False
        
        if day and day in schedule:
            for event in schedule[day]:
                time_range = event.get('time')
                description = event.get('description', '')
                if not time_range:
                    logger.warning("Event missing 'time': %s", event)
                    continue
                try:
                    event_time = datetime.strptime(time_range, "%H:%M-%H:%M").replace(year=specific_time.year, month=specific_time.month, day=specific_time.day)
                    if event_time == specific_time:
                        output += f"- {time_range}: {description}\n"
                        found = True
                except (ValueError, TypeError):
                    pass
        elif not day:
            current_day = specific_time.strftime("%A")
            if current_day in schedule:
                for event in schedule[current_day]:
                    time_range = event.get('time')
                    description = event.get('description', '')
                    if not time_range:
                        logger.warning("Event missing 'time': %s", event)
                        continue
                    try:
                        event_time = datetime.strptime(time_range, "%H:%M-%H:%M").replace(year=specific_time.year, month=specific_time.month, day=specific_time.day)
                        if event_time == specific_time:
                            output += f"- {time_range}: {description}\n"
                            found = True
                    except (ValueError, TypeError):
                        pass

        if found:
            return output
        else:
            no_events_msg = self.lang_manager.translate(
                guild_id, "system", "schedule", "format", "no_events_found"
            ) if self.lang_manager else "沒有找到該時間的行程。"
            return no_events_msg

    def format_next_schedule(self, schedule, now, guild_id="0"):
        next_event = None
        for day, events in schedule.items():
            for event in events:
                event_time_str = event.get('time')
                description = event.get('description', '')
                if not event_time_str or '-' not in event_time_str:
                    logger.warning("Invalid or missing event time: %s", event)
                    continue
                try:
                    start_time_str, end_time_str = event_time_str.split('-', 1)
                    start_time = datetime.strptime(start_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                    end_time = datetime.strptime(end_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                    if start_time > now:
                        if next_event is None or start_time < next_event[0]:
                            next_event = (start_time, description)
                except (ValueError, TypeError):
                    pass
        
        if next_event:
            return self.lang_manager.translate(
                guild_id, "system", "schedule", "format", "next_event",
                time=next_event[0].strftime('%H:%M'), description=next_event[1]
            ) if self.lang_manager else f"下一個行程：{next_event[0].strftime('%H:%M')} - {next_event[1]}"
        else:
            return self.lang_manager.translate(
                guild_id, "system", "schedule", "format", "no_next_event"
            ) if self.lang_manager else "沒有找到下一個行程。"

    @app_commands.command(name="update_schedule", description="Add or change an event in your schedule")
    @app_commands.describe(day="Day of the week", time="Time range, e.g. 09:00-10:30", description="What happens then")
    @app_commands.choices(day=DAY_CHOICES)
    async def update_schedule_command(self, interaction: discord.Interaction, day: app_commands.Choice[str], time: str, description: str):
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        time_range = normalize_time_range(time)
        if time_range is None:
            await interaction.response.send_message(
                self.lang_manager.translate(guild_id, "commands", "update_schedule", "responses", "invalid_time"),
                ephemeral=True,
            )
            return
        await interaction.response.defer(thinking=True)
        
        try:
            await self._core_update_schedule(interaction.user.id, day.value, time_range, description, interaction.channel_id)
            success_msg = self.lang_manager.translate(
                guild_id, "commands", "update_schedule", "responses", "success"
            ) if self.lang_manager else "行程表已成功更新或創建！"
            await interaction.edit_original_response(content=success_msg)
        except Exception as e:
            await func.report_error(e, "updating schedule")
            error_msg = self.lang_manager.translate(
                guild_id, "commands", "update_schedule", "responses", "error", error=str(e)
            ) if self.lang_manager else f"更新或創建行程表時發生錯誤：{str(e)}"
            await interaction.edit_original_response(content=error_msg)

    async def _core_update_schedule(self, user_id: int, day: str, time: str, description: str, channel_id: int = 0):
        filepath = os.path.join(self.schedule_dir, f"{user_id}.yaml")
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump({"channel_id": channel_id or 0, "schedule": {}}, f)

        with open(filepath, "r", encoding='utf-8') as f:
            schedule_data = yaml.safe_load(f)
        if schedule_data is None:
            schedule_data = {}
        schedule_data, repaired = self._sanitize_schedule_data(schedule_data, schedule_data.get('channel_id', 0) if isinstance(schedule_data, dict) else 0)
        if repaired:
            with open(filepath, "w", encoding='utf-8') as fw:
                yaml.dump(schedule_data, fw, allow_unicode=True)
        schedule = schedule_data.get("schedule", {})

        # Reuse the existing key for this day whatever its case ("Monday" vs "monday").
        day_key = next((k for k in schedule if str(k).strip().casefold() == day.strip().casefold()), day)
        events = schedule.setdefault(day_key, [])
        # Fill the slot with the same time if there is one (as in the template), else add a new one.
        for event in events:
            if isinstance(event, dict) and normalize_time_range(str(event.get("time", ""))) == normalize_time_range(time):
                event["description"] = description
                break
        else:
            events.append({"time": time, "description": description})

        schedule_data["schedule"] = schedule
        with open(filepath, "w", encoding='utf-8') as f:
            yaml.dump(schedule_data, f, allow_unicode=True)

    @app_commands.command(name="show_template", description="Show the schedule template")
    async def show_template_command(self, interaction: discord.Interaction) -> None:
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        with open(os.path.join(self.schedule_dir, "template.yaml"), "r", encoding='utf-8') as f:
            template = f.read()
            
        message_content = f"```yaml\n{template}\n```"
        if len(message_content) > 2000:
            import io
            file = discord.File(io.BytesIO(template.encode("utf-8")), filename="template.yaml")
            success_msg = self.lang_manager.translate(
                guild_id, "commands", "show_template", "responses", "file_sent"
            ) if self.lang_manager else "行程表範本已作為檔案發送！"
            await interaction.response.send_message(content=success_msg, file=file)
        else:
            await interaction.response.send_message(message_content)


async def setup(bot):
    await bot.add_cog(ScheduleManager(bot))
