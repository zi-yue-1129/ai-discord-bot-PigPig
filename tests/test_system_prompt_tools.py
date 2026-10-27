"""Tests for llm/tools/system_prompt_tools.py."""
import sys
import types
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# ── Stub heavy dependencies ──────────────────────────────────────────────────

class _DummyLogger:
    def info(self, *a, **kw): pass
    def warning(self, *a, **kw): pass
    def error(self, *a, **kw): pass
    def debug(self, *a, **kw): pass
    def bind(self, **kw): return self

fake_addons = types.ModuleType("addons")
fake_addons.__path__ = [str(project_root / "addons")]
fake_logging_mod = types.ModuleType("addons.logging")
fake_logging_mod.get_logger = lambda **kwargs: _DummyLogger()
fake_settings_mod = types.ModuleType("addons.settings")
fake_settings_mod.update_config = types.SimpleNamespace(github={})
fake_addons.logging = fake_logging_mod
fake_addons.settings = fake_settings_mod
sys.modules.setdefault("addons", fake_addons)
sys.modules.setdefault("addons.logging", fake_logging_mod)
sys.modules.setdefault("addons.settings", fake_settings_mod)

fake_function = types.ModuleType("function")
fake_function.func = types.SimpleNamespace(report_error=AsyncMock(return_value=None))
sys.modules.setdefault("function", fake_function)

# Stub langchain_core
fake_lc = types.ModuleType("langchain_core")
fake_lc.__path__ = []
fake_tools = types.ModuleType("langchain_core.tools")
fake_tools.__path__ = []
fake_structured = types.ModuleType("langchain_core.tools.structured")

class _FakeStructuredTool:
    def __init__(self, name, coroutine, description, metadata):
        self.name = name
        self.coroutine = coroutine
        self.description = description
        self.metadata = metadata or {}

    @classmethod
    def from_function(cls, func, name, coroutine, description, metadata=None):
        return cls(name=name, coroutine=coroutine, description=description, metadata=metadata)

fake_structured.StructuredTool = _FakeStructuredTool
sys.modules.setdefault("langchain_core", fake_lc)
sys.modules.setdefault("langchain_core.tools", fake_tools)
sys.modules.setdefault("langchain_core.tools.structured", fake_structured)

# Stub cogs.system_prompt.permissions
fake_cogs = types.ModuleType("cogs")
fake_cogs.__path__ = []
fake_sp = types.ModuleType("cogs.system_prompt")
fake_sp.__path__ = []
fake_perm_mod = types.ModuleType("cogs.system_prompt.permissions")

class FakePermissionValidator:
    def __init__(self, bot): pass
    def can_modify_server_prompt(self, user, guild, config=None): return False
    def can_modify_channel_prompt(self, user, channel, config=None): return True

fake_perm_mod.PermissionValidator = FakePermissionValidator
fake_sp.permissions = fake_perm_mod

fake_sp_exc = types.ModuleType("cogs.system_prompt.exceptions")
class _FakeContentTooLongError(Exception): pass
class _FakeUnsafeContentError(Exception): pass
fake_sp_exc.ContentTooLongError = _FakeContentTooLongError
fake_sp_exc.UnsafeContentError = _FakeUnsafeContentError

sys.modules.setdefault("cogs", fake_cogs)
sys.modules.setdefault("cogs.system_prompt", fake_sp)
sys.modules.setdefault("cogs.system_prompt.permissions", fake_perm_mod)
sys.modules.setdefault("cogs.system_prompt.exceptions", fake_sp_exc)

# Now safe to import
from llm.tools.system_prompt_tools import SystemPromptTools, check_personality_permission  # noqa: E402


def _make_runtime(guild_id=111, channel_id=222, author_id=333, bot=None):
    msg = MagicMock()
    msg.guild.id = guild_id
    msg.channel.id = channel_id
    msg.author.id = author_id
    runtime = MagicMock()
    runtime.message = msg
    runtime.bot = bot or MagicMock()
    return runtime


def _make_bot_with_manager(set_channel_return=True, set_server_return=True):
    mock_manager = MagicMock()
    mock_manager.set_channel_prompt.return_value = set_channel_return
    mock_manager.set_server_prompt.return_value = set_server_return
    mock_manager.cache = MagicMock()
    mock_cog = MagicMock()
    mock_cog.get_system_prompt_manager.return_value = mock_manager
    mock_bot = MagicMock()
    mock_bot.get_cog.return_value = mock_cog
    return mock_bot, mock_manager


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_get_tools_returns_one_tool():
    """SystemPromptTools.get_tools returns exactly one tool named update_personality."""
    runtime = _make_runtime()
    tools = SystemPromptTools(runtime).get_tools()
    assert len(tools) == 1
    assert tools[0].name == "update_personality"


def test_tool_target_agent_mode_is_message():
    """update_personality tool has target_agent_mode=message in metadata."""
    runtime = _make_runtime()
    tool = SystemPromptTools(runtime).get_tools()[0]
    assert tool.metadata.get("target_agent_mode") == "message"


def test_write_personality_exported():
    """write_personality is exported from the module."""
    import llm.tools.system_prompt_tools as mod
    assert "write_personality" in mod.__all__
    assert "SystemPromptTools" in mod.__all__


def _ask_and_press(tool, **kwargs):
    """Runs the tool, then presses Confirm on the question it posted; returns (tool reply, press reply, asks)."""
    asks = []

    async def fake_ask(channel, content, view):
        asks.append((content, view))
        return view

    async def run():
        with patch("addons.confirm.ask", fake_ask):
            reply = await tool.coroutine(**kwargs)
        pressed = await asks[0][1].on_confirm() if asks else None
        return reply, pressed

    reply, pressed = asyncio.run(run())
    return reply, pressed, asks


class TestUpdatePersonalityChannel:
    def setup_method(self):
        self.mock_bot, self.mock_manager = _make_bot_with_manager()
        self.mock_bot.personality_asks = {}
        self.runtime = _make_runtime(bot=self.mock_bot)
        self.tool = SystemPromptTools(self.runtime).get_tools()[0]

    def test_nothing_is_written_before_the_member_presses_confirm(self):
        async def run():
            async def fake_ask(channel, content, view):
                return view
            with patch("addons.confirm.ask", fake_ask):
                return await self.tool.coroutine(merged_prompt="Be funny.", scope="channel")

        reply = asyncio.run(run())
        assert "confirm" in reply.lower()
        self.mock_manager.set_channel_prompt.assert_not_called()

    def test_only_the_asking_member_may_press(self):
        _, _, asks = _ask_and_press(self.tool, merged_prompt="Be funny.", scope="channel")
        assert asks[0][1].owner_id == 333

    def test_the_proposal_is_shown_with_the_question(self):
        _, _, asks = _ask_and_press(self.tool, merged_prompt="Be funny.", scope="channel")
        assert "> Be funny." in asks[0][0]

    def test_calls_set_channel_prompt_with_correct_args(self):
        _ask_and_press(self.tool, merged_prompt="Be funny.", scope="channel")
        self.mock_manager.set_channel_prompt.assert_called_once_with(
            "111", "222", {"prompt": "Be funny.", "enabled": True}, "333"
        )

    def test_invalidates_cache_after_write(self):
        _ask_and_press(self.tool, merged_prompt="Be funny.", scope="channel")
        self.mock_manager.cache.invalidate.assert_called()

    def test_a_member_who_lost_the_permission_cannot_confirm(self):
        asks = []

        async def fake_ask(channel, content, view):
            asks.append(view)
            return view

        async def run():
            with patch("addons.confirm.ask", fake_ask):
                await self.tool.coroutine(merged_prompt="Be rude.", scope="channel")
            with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
                MockV.return_value.can_modify_channel_prompt.return_value = False
                return await asks[0].on_confirm()

        asyncio.run(run())
        self.mock_manager.set_channel_prompt.assert_not_called()


class TestUpdatePersonalityServer:
    def setup_method(self):
        self.mock_bot, self.mock_manager = _make_bot_with_manager()
        self.mock_bot.personality_asks = {}
        self.runtime = _make_runtime(bot=self.mock_bot)
        self.tool = SystemPromptTools(self.runtime).get_tools()[0]

    def test_blocks_non_admin_from_server_scope(self):
        with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
            MockV.return_value.can_modify_server_prompt.return_value = False
            result = asyncio.run(
                self.tool.coroutine(merged_prompt="...", scope="server")
            )
        assert "permission" in result.lower() or "administrator" in result.lower()

    def test_allows_admin_to_set_server_scope(self):
        with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
            MockV.return_value.can_modify_server_prompt.return_value = True
            _ask_and_press(self.tool, merged_prompt="Be formal.", scope="server")
        self.mock_manager.set_server_prompt.assert_called_once_with(
            "111", {"prompt": "Be formal.", "enabled": True}, "333"
        )


class TestUpdatePersonalityErrors:
    def test_missing_cog_saves_nothing(self):
        mock_bot = MagicMock()
        mock_bot.get_cog.return_value = None
        mock_bot.personality_asks = {}
        runtime = _make_runtime(bot=mock_bot)
        tool = SystemPromptTools(runtime).get_tools()[0]
        _, pressed, _ = _ask_and_press(tool, merged_prompt="...", scope="channel")
        assert "nothing changed" in pressed.lower()

    def test_no_message_context_returns_error_string(self):
        runtime = MagicMock()
        runtime.message = None
        tool = SystemPromptTools(runtime).get_tools()[0]
        result = asyncio.run(
            tool.coroutine(merged_prompt="...", scope="channel")
        )
        assert "error" in result.lower()


class TestUpdatePersonalityChannelPermission:
    """Channel-scope writes require channel management permission."""

    def setup_method(self):
        self.mock_bot, self.mock_manager = _make_bot_with_manager()
        self.runtime = _make_runtime(bot=self.mock_bot)
        self.tool = SystemPromptTools(self.runtime).get_tools()[0]

    def test_blocks_user_without_channel_permission(self):
        with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
            MockV.return_value.can_modify_channel_prompt.return_value = False
            result = asyncio.run(
                self.tool.coroutine(merged_prompt="Be rude.", scope="channel")
            )
        assert result.startswith("Error")
        self.mock_manager.set_channel_prompt.assert_not_called()

    def test_blocks_unrecognised_scope_without_channel_permission(self):
        """Any non-server scope falls through to a channel write, so it must be checked too."""
        with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
            MockV.return_value.can_modify_channel_prompt.return_value = False
            result = asyncio.run(
                self.tool.coroutine(merged_prompt="Be rude.", scope="Channel")
            )
        assert result.startswith("Error")
        self.mock_manager.set_channel_prompt.assert_not_called()

    def test_tool_description_does_not_claim_any_user_may_modify(self):
        assert "any user" not in self.tool.description.lower()


class TestCheckPersonalityPermission:
    """Shared permission helper used by both the tool and the slash command."""

    def test_server_scope_requires_server_permission(self):
        with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
            MockV.return_value.can_modify_server_prompt.return_value = False
            error = check_personality_permission(MagicMock(), MagicMock(), MagicMock(), MagicMock(), "server")
        assert error is not None and "administrator" in error.lower()

    def test_channel_scope_allowed_with_channel_permission(self):
        with patch("cogs.system_prompt.permissions.PermissionValidator") as MockV:
            MockV.return_value.can_modify_channel_prompt.return_value = True
            error = check_personality_permission(MagicMock(), MagicMock(), MagicMock(), MagicMock(), "channel")
        assert error is None
