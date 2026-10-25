"""Tool that lets the AI look up how the bot itself works.

The answer is generated from the loaded cogs, the registered tools and the attachment
settings (see :mod:`llm.self_knowledge`), so it never needs a hand-kept list. The tool runs
in the info agent.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from langchain_core.tools import BaseTool
from langchain_core.tools.structured import StructuredTool

from addons.settings import memory_config
from llm import tools_factory
from llm.self_knowledge import build_guide, collect_commands

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_DESCRIPTION = (
    "Look up how this bot works: its slash commands (what each one does and how to fill it in), "
    "the abilities it uses while chatting, and which kinds of content it can see.\n"
    "Call it when a user asks what the bot can do, how to use a command or feature, or whether "
    "it can read or see something such as images, PDFs, videos or other files.\n"
    "Pass `topic` as a command name, a feature word or an ability name; leave it empty for the "
    "full overview. Answer from the result and do not guess."
)


class BotGuideTools:
    """Container for the tool that explains the bot to its users."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        """Keep the request runtime; the bot and the asking user are read when the tool runs.

        Args:
            runtime: The current orchestrator request.
        """
        self.runtime = runtime

    def get_tools(self) -> List[BaseTool]:
        """Return the guide tool.

        Returns:
            A list with the single ``get_bot_guide`` tool, routed to the info agent.
        """
        runtime = self.runtime

        async def get_bot_guide(topic: str = "") -> str:
            """Return what the bot can tell about itself for ``topic``.

            Args:
                topic: Command name, feature word or ability name; empty for the overview.

            Returns:
                Text built from the live commands, tools and attachment settings.
            """
            message = runtime.message
            tools = tools_factory.get_tools(message.author, message.guild, runtime, agent_mode="all")
            return build_guide(topic, collect_commands(runtime.bot), tools, memory_config.short_term_limit)

        return [
            StructuredTool.from_function(
                func=None,
                coroutine=get_bot_guide,
                name="get_bot_guide",
                description=_DESCRIPTION,
                metadata={"target_agent_mode": "info"},
            )
        ]
